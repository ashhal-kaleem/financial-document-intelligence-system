"""Script to evaluate answer quality.

Metric Definitions
------------------
context_recall
    For each answerable question, the fraction of ``expected_answer_facts``
    that appear (case-insensitive substring) in the concatenated retrieved
    chunks.  A score of 1.0 means the retriever surfaced all expected facts.

factual_correctness
    For each answerable question, the fraction of ``expected_answer_facts``
    that appear (case-insensitive substring) in the generated answer.  This
    is a deterministic check -- no LLM judge involved.

groundedness (LLM judge)
    For each answerable question, a YES/NO verdict from a zero-temperature
    LLM call asking "is every factual claim in the ANSWER supported by the
    CONTEXT?"  Measures hallucination, not factual accuracy.

    **Known limitation**: the judge is the same model family as the generator,
    which can create a self-serving bias.  Treat this as a soft signal.

unanswerable_handling
    For questions where ``answerable`` is false, whether the system correctly
    refuses to answer (detects no relevant context).  Checked via keyword
    matching in the generated answer.
"""
import json
import time
from pathlib import Path

from financial_rag.config import settings
from financial_rag.pipeline.factory import create_pipeline


# ── Helpers ────────────────────────────────────────────────────────────────────

def fact_in_text(fact: str, text: str) -> bool:
    """Case-insensitive substring match."""
    return fact.lower() in text.lower()


# Phrases that indicate the model is refusing/declining to answer.
_REFUSAL_PHRASES = [
    "no context",
    "no information",
    "cannot find",
    "do not know",
    "i don't know",
    "not mentioned",
    "not provided",
    "cannot answer",
    "not available",
    "don't have",
    "no details",
]


def is_refusal(text: str) -> bool:
    t = text.lower()
    return any(p in t for p in _REFUSAL_PHRASES)


def llm_judge_groundedness(generator, answer: str, context: str) -> bool:
    """Ask the LLM: is the answer fully grounded in the context?

    Returns True  -> grounded (no hallucination detected)
    Returns False -> at least one claim not supported by context
    """
    if not answer or not context:
        return False

    prompt = (
        "You are a strict factual grounding evaluator.\n"
        "Determine whether EVERY factual claim in the ANSWER is explicitly "
        "supported by the CONTEXT below.\n"
        "Answer 'YES' only if ALL facts in the ANSWER are supported.\n"
        "Answer 'NO' if ANY fact is not supported or is hallucinated.\n\n"
        f"CONTEXT:\n{context}\n\n"
        f"ANSWER:\n{answer}\n\n"
        "Respond with only YES or NO."
    )

    try:
        import groq as groq_lib
        for attempt in range(5):
            try:
                response = generator._client.chat.completions.create(
                    model=generator._model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0,
                    max_tokens=10,
                )
                result = response.choices[0].message.content.strip().upper()
                return result.startswith("YES")
            except groq_lib.RateLimitError:
                wait = 2 ** attempt
                print(f"    [judge rate limit] retry {attempt+1}/5 in {wait}s")
                time.sleep(wait)
        return False
    except Exception as exc:
        print(f"    [LLM judge error] {exc}")
        return False


def pipeline_ask_with_retry(pipeline, question: str, kwargs: dict, max_retries: int = 6):
    """Call pipeline.ask() with exponential backoff on rate-limit errors."""
    import groq as groq_lib
    for attempt in range(max_retries):
        try:
            return pipeline.ask(question, **kwargs)
        except groq_lib.RateLimitError as exc:
            wait = 2 ** attempt
            print(f"    [rate limit] retry {attempt+1}/{max_retries} in {wait}s")
            time.sleep(wait)
        except Exception as exc:
            print(f"    [unexpected pipeline error] {exc}")
            return None
    
    print(f"    [ERROR] Rate limit persisted after {max_retries} retries for: {question!r}")
    return None


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    dataset_path = Path("scripts/evaluation_dataset.json")
    if not dataset_path.exists():
        print(f"Error: {dataset_path} not found.")
        return

    with open(dataset_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # Strip comment-only entries
    dataset = [item for item in raw if "id" in item]

    pipeline = create_pipeline(
        store_path="data/processed/vector_store",
        model=settings.groq_model,
        api_key=settings.groq_api_key,
        backend=settings.vector_store,
        supabase_url=settings.supabase_url,
        supabase_key=settings.supabase_key,
        supabase_table=settings.supabase_table,
        supabase_rpc=settings.supabase_rpc,
    )

    print("=" * 52)
    print("RAG ANSWER EVALUATION")
    print("=" * 52)
    print(f"Total questions   : {len(dataset)}\n")

    # Per-metric accumulators
    context_recall_scores: list[float] = []
    correctness_scores: list[float] = []
    groundedness_scores: list[float] = []
    unanswerable_scores: list[float] = []

    results = []

    for item in dataset:
        q_id       = item["id"]
        question   = item["question"]
        expected   = item.get("expected_answer_facts", [])
        answerable = item.get("answerable", True)
        doc_ids    = item.get("document_ids")
        category   = item.get("category", "unknown")

        print(f"  [{q_id}] {question[:65]}...")

        kwargs: dict = {"top_k": 5}
        if doc_ids is not None:
            kwargs["document_ids"] = doc_ids

        response        = pipeline_ask_with_retry(pipeline, question, kwargs)
        if response is None:
            print("    [ERROR] Skipping evaluation due to API failure.")
            row = {
                "id": q_id,
                "category": category,
                "answerable": answerable,
                "error": "API Failure",
            }
            results.append(row)
            continue
            
        combined_ctx    = "\n".join(response.chunk_texts)
        answer          = response.answer

        row: dict = {
            "id": q_id,
            "category": category,
            "answerable": answerable,
            "answer": answer,
        }

        if not answerable:
            # Unanswerable handling
            refused = is_refusal(answer)
            score   = 1.0 if refused else 0.0
            unanswerable_scores.append(score)
            row["unanswerable_handling"] = score
            tag = "[REFUSED]" if refused else "[HALLUCINATED]"
            print(f"    unanswerable_handling: {tag}")
        else:
            # Context recall (deterministic)
            ctx_recall: float | None = None
            if expected:
                ctx_recall = sum(
                    1 for f in expected if fact_in_text(f, combined_ctx)
                ) / len(expected)
                context_recall_scores.append(ctx_recall)

            # Factual correctness (deterministic)
            correctness: float | None = None
            if expected:
                correctness = sum(
                    1 for f in expected if fact_in_text(f, answer)
                ) / len(expected)
                correctness_scores.append(correctness)

            # Groundedness (LLM judge)
            is_grounded = llm_judge_groundedness(pipeline._generator, answer, combined_ctx)
            groundedness = 1.0 if is_grounded else 0.0
            groundedness_scores.append(groundedness)

            row["context_recall"]     = ctx_recall
            row["factual_correctness"] = correctness
            row["groundedness"]       = groundedness

            print(
                f"    ctx_recall={ctx_recall:.2f}  "
                f"correctness={correctness:.2f}  "
                f"grounded={'[YES]' if is_grounded else '[NO]'}"
            )

        results.append(row)

        # Throttle to avoid rate limits (longer pause to reduce 429s)
        time.sleep(3.0)

    # Aggregate
    def _avg(lst: list[float]) -> float | None:
        return sum(lst) / len(lst) if lst else None

    avg_ctx_recall   = _avg(context_recall_scores)
    avg_correctness  = _avg(correctness_scores)
    avg_groundedness = _avg(groundedness_scores)
    avg_unanswerable = _avg(unanswerable_scores)

    answerable_n   = sum(1 for i in dataset if i.get("answerable", True) and "id" in i)
    unanswerable_n = sum(1 for i in dataset if not i.get("answerable", True) and "id" in i)

    print()
    print("=" * 52)
    print("ANSWER EVALUATION SUMMARY")
    print("=" * 52)
    print(f"  Questions            : {len(dataset)}")
    print(f"  Answerable           : {answerable_n}")
    print(f"  Unanswerable         : {unanswerable_n}")
    print()
    print("Metrics (answerable questions):")
    if avg_ctx_recall is not None:
        print(f"  Context recall       : {avg_ctx_recall:.2f}")
    if avg_correctness is not None:
        print(f"  Factual correctness  : {avg_correctness:.2f}")
    if avg_groundedness is not None:
        print(f"  Groundedness (LLM)   : {avg_groundedness:.2f}")
    if avg_unanswerable is not None:
        print(f"  Unanswerable handling: {avg_unanswerable:.2f}")

    print()
    print("Metric definitions:")
    print("  context_recall      = fraction of expected_facts found in retrieved chunks")
    print("  factual_correctness = fraction of expected_facts found in the answer")
    print("  groundedness        = LLM judge YES/NO (is every answer claim in context?)")
    print("  unanswerable_handling = fraction of n/a Qs where system refused")

    # Save
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    report_file = reports_dir / "answer_evaluation.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "metric_definitions": {
                    "context_recall":       "Fraction of expected facts present in retrieved chunks (deterministic substring match)",
                    "factual_correctness":  "Fraction of expected facts present in the generated answer (deterministic substring match)",
                    "groundedness":         "LLM judge: YES if ALL answer claims supported by context, NO otherwise (soft signal -- same model family as generator)",
                    "unanswerable_handling":"Fraction of unanswerable questions where the system correctly refused to answer",
                },
                "metrics": {
                    "context_recall":       avg_ctx_recall,
                    "factual_correctness":  avg_correctness,
                    "groundedness":         avg_groundedness,
                    "unanswerable_handling":avg_unanswerable,
                },
                "counts": {
                    "total":       len(dataset),
                    "answerable":  answerable_n,
                    "unanswerable":unanswerable_n,
                },
                "results": results,
            },
            f,
            indent=2,
        )
    print(f"\nSaved report to {report_file}")


if __name__ == "__main__":
    main()
