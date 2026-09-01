"""Script to evaluate retrieval performance of the RAG system.

Metrics reported
----------------
Recall@K  : fraction of answerable questions where the first relevant source
            appears in the top-K ranked results.
MRR       : Mean Reciprocal Rank across all answerable questions.
Avg rank  : Average first-relevant-rank (over questions where rank <= 10).

Note: questions with ``"answerable": false`` are excluded from all metrics
but are counted and reported as "skipped".
"""
import json
import os
from pathlib import Path

from financial_rag.config import settings
from financial_rag.pipeline.factory import create_pipeline


# ── Metric helpers ─────────────────────────────────────────────────────────────

def calculate_mrr(ranks: list[int | float]) -> float:
    """MRR over all questions (inf ranks contribute 0)."""
    if not ranks:
        return 0.0
    return sum(1.0 / r for r in ranks if r != float("inf")) / len(ranks)


def calculate_recall_at_k(ranks: list[int | float], k: int) -> float:
    if not ranks:
        return 0.0
    return sum(1 for r in ranks if r <= k) / len(ranks)


def avg_first_relevant_rank(ranks: list[int | float]) -> float:
    finite = [r for r in ranks if r != float("inf")]
    return sum(finite) / len(finite) if finite else float("inf")


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

    # Partition
    answerable = [item for item in dataset if item.get("answerable", True) and item.get("expected_sources")]
    unanswerable = [item for item in dataset if not item.get("answerable", True) or not item.get("expected_sources")]

    # Initialize retriever
    pipeline = create_pipeline(
        store_path="data/processed/vector_store",
        model="llama-3.3-70b-versatile",
        api_key=settings.groq_api_key,
        backend=settings.vector_store,
        supabase_url=settings.supabase_url,
        supabase_key=settings.supabase_key,
        supabase_table=settings.supabase_table,
        supabase_rpc=settings.supabase_rpc,
    )
    retriever = pipeline._retriever

    use_reranker = os.environ.get("USE_RERANKER", str(settings.use_reranker)).lower() in ("1", "true", "yes")

    print("=" * 48)
    print("RAG RETRIEVAL EVALUATION")
    print("=" * 48)
    print(f"Reranker          : {'ON' if use_reranker else 'OFF'}")
    print(f"Total questions   : {len(dataset)}")
    print(f"Answerable        : {len(answerable)}")
    print(f"Skipped (n/a)     : {len(unanswerable)}")
    print()
    print("Per-question results:")

    first_relevant_ranks: list[int | float] = []
    results = []
    not_rank_1 = 0

    for item in answerable:
        q_id = item["id"]
        question = item["question"]
        expected_sources = item["expected_sources"]
        document_ids = item.get("document_ids")
        category = item.get("category", "unknown")

        kwargs: dict = {"top_k": 10}
        if document_ids is not None:
            kwargs["document_ids"] = document_ids

        retrieval_res = retriever.retrieve(question, **kwargs)

        rank: int | float = float("inf")
        for i, scored in enumerate(retrieval_res.results):
            if scored.chunk.source in expected_sources:
                rank = i + 1
                break

        first_relevant_ranks.append(rank)

        if rank == float("inf"):
            status = "FAIL"
            print(f"  {q_id:<4}  [{category:<25}]  FAIL  (not in top 10)")
        else:
            status = "PASS"
            tag = " <-- not rank 1" if rank > 1 else ""
            print(f"  {q_id:<4}  [{category:<25}]  PASS  rank={rank}{tag}")
            if rank > 1:
                not_rank_1 += 1

        results.append({
            "id": q_id,
            "category": category,
            "question": question,
            "status": status,
            "rank": rank if rank != float("inf") else None,
        })

    # ── Rank distribution ──────────────────────────────────────────────────────
    finite_ranks = [r for r in first_relevant_ranks if r != float("inf")]
    rank_dist: dict[int, int] = {}
    for r in finite_ranks:
        rank_dist[int(r)] = rank_dist.get(int(r), 0) + 1

    # ── Summary ────────────────────────────────────────────────────────────────
    recall_1  = calculate_recall_at_k(first_relevant_ranks, 1)
    recall_3  = calculate_recall_at_k(first_relevant_ranks, 3)
    recall_5  = calculate_recall_at_k(first_relevant_ranks, 5)
    recall_10 = calculate_recall_at_k(first_relevant_ranks, 10)
    mrr       = calculate_mrr(first_relevant_ranks)
    avg_rank  = avg_first_relevant_rank(first_relevant_ranks)

    failed    = sum(1 for r in first_relevant_ranks if r == float("inf"))

    print()
    print("=" * 48)
    print(f"Recall@1           : {recall_1:.2f}")
    print(f"Recall@3           : {recall_3:.2f}")
    print(f"Recall@5           : {recall_5:.2f}")
    print(f"Recall@10          : {recall_10:.2f}")
    print(f"MRR                : {mrr:.2f}")
    print(f"Avg first rank     : {avg_rank:.2f}")
    print()
    print(f"Not at rank 1      : {not_rank_1}/{len(answerable)}")
    print(f"Not in top 10      : {failed}/{len(answerable)}")
    print()
    print("Rank distribution  :", " | ".join(f"rank {k}: {v}" for k, v in sorted(rank_dist.items())))

    # ── Save report ────────────────────────────────────────────────────────────
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    report_file = reports_dir / "retrieval_evaluation.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "reranker": use_reranker,
                "metrics": {
                    "recall_1":  recall_1,
                    "recall_3":  recall_3,
                    "recall_5":  recall_5,
                    "recall_10": recall_10,
                    "mrr":       mrr,
                    "avg_first_relevant_rank": avg_rank if avg_rank != float("inf") else None,
                    "not_rank_1": not_rank_1,
                    "not_in_top10": failed,
                    "answerable_questions": len(answerable),
                    "skipped_questions": len(unanswerable),
                },
                "rank_distribution": rank_dist,
                "results": results,
            },
            f,
            indent=2,
        )
    print(f"\nSaved report to {report_file}")


if __name__ == "__main__":
    main()
