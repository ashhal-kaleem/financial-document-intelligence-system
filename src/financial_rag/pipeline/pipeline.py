"""RAG pipeline — chains retriever and generator into a single ask() call."""

import time

from financial_rag.generation.base import BaseGenerator
from financial_rag.generation.models import ConversationTurn, GenerationResult
from financial_rag.pipeline.models import RAGResponse
from financial_rag.retrieval.base import BaseRetriever
from financial_rag.config import settings


class RAGPipeline:
    """End-to-end RAG pipeline: retrieve relevant chunks, then generate an answer.

    This is the single entry point for the application layer (API, UI).
    All latency measurement, logging hooks, and future caching live here.

    Args:
        retriever: Any BaseRetriever implementation.
        generator: Any BaseGenerator implementation.
        top_k: Default number of chunks to pass to the generator.
        top_k: Default number of chunks to pass to the generator.
    """

    def __init__(
        self,
        retriever: BaseRetriever,
        generator: BaseGenerator,
        top_k: int = 5,
    ) -> None:
        self._retriever = retriever
        self._generator = generator
        self._top_k = top_k

    def ask(
        self,
        question: str,
        top_k: int | None = None,
        source_filter: str | None = None,
        document_ids: list[str] | None = None,
        history: list[ConversationTurn] | None = None,
        model: str | None = None,
    ) -> RAGResponse:
        """Answer a question using retrieved context.

        Args:
            question: Natural language question.
            top_k: Override the default number of chunks to retrieve.
            source_filter: Restrict retrieval to a specific source
                (e.g. "interbank", "scotiabank"). Passed to the retriever
                if it supports it — silently ignored otherwise.

        Returns:
            RAGResponse with the answer, citations, scores, and latency breakdown.
        """
        k = top_k if top_k is not None else self._top_k

        # ── Retrieval ──────────────────────────────────────────────────────
        t0 = time.perf_counter()
        retrieve_kwargs: dict = {"top_k": k}
        if source_filter is not None:
            retrieve_kwargs["source_filter"] = source_filter
        if document_ids is not None:
            retrieve_kwargs["document_ids"] = document_ids
        retrieval = self._retriever.retrieve(question, **retrieve_kwargs)

        retrieval_ms = (time.perf_counter() - t0) * 1000

        # ── Evidence Gate (Fast LLM Check) ─────────────────────────────────
        if retrieval.is_empty:
            return RAGResponse(
                answer="I couldn't find enough information in the available documents to answer that question reliably.",
                query=question,
                citations=[],
                retrieval_scores=[],
                chunks_used=0,
                model="abstention",
                retrieval_ms=retrieval_ms,
                generation_ms=0.0,
                chunk_texts=[],
            )

        t_gate0 = time.perf_counter()
        gate_ms = 0.0
        
        # ── Threshold fast-path ────────────────────────────────────────────
        # Using 0.65 as upper threshold for definitely answerable
        # Using 0.30 as lower threshold for definitely unanswerable
        is_supported = True
        if hasattr(self._generator, "_client"):
            max_score = max(r.score for r in retrieval.results) if retrieval.results else 0.0
            
            if max_score < 0.30:
                is_supported = False
            elif max_score >= 0.65:
                is_supported = True
            else:
                # ── Borderline case: Use LLM Gate ──────────────────────────────
                # Build combined context
                lines = ["Context:"]
                for i, result in enumerate(retrieval.results, start=1):
                    lines.append(f"[{i}] {result.citation}")
                    lines.append(result.chunk.content.strip())
                    lines.append("")
                combined_ctx = "\n".join(lines)

                gate_prompt = (
                    "Determine if the provided CONTEXT contains sufficient information to answer the QUESTION.\n"
                    "Answer 'YES' if the context has the facts to answer the question, even partially.\n"
                    "Answer 'NO' if the context is completely unrelated or insufficient.\n\n"
                    f"CONTEXT:\n{combined_ctx}\n\n"
                    f"QUESTION:\n{question}\n\n"
                    "Respond with only YES or NO."
                )

                try:
                    import groq as groq_lib
                    for attempt in range(4):
                        try:
                            gate_resp = self._generator._client.chat.completions.create(
                                model=settings.groq_model,  # Fast model for gating
                                messages=[{"role": "user", "content": gate_prompt}],
                                temperature=0.0,
                                max_tokens=10,
                            )
                            gate_result = gate_resp.choices[0].message.content.strip().upper()
                            is_supported = gate_result.startswith("YES")
                            break
                        except groq_lib.RateLimitError:
                            if attempt == 3:
                                raise
                            time.sleep(2 ** attempt)
                except Exception as exc:
                    # Let API errors bubble up to routes.py so they can return 429/503
                    import groq as groq_lib
                    if isinstance(exc, (groq_lib.RateLimitError, groq_lib.APIError, groq_lib.APIConnectionError)):
                        raise
                    print(f"Evidence Gate Error (non-API): {exc}")
                    # If it's a local logic error or similar, default to allowing generation
                    is_supported = True
            
        gate_ms = (time.perf_counter() - t_gate0) * 1000

        if not is_supported:
            return RAGResponse(
                answer="I couldn't find enough information in the available documents to answer that question reliably.",
                query=question,
                citations=[],
                retrieval_scores=[r.score for r in retrieval.results],
                chunks_used=retrieval.total,
                model=f"{settings.groq_model} (gate)",
                retrieval_ms=retrieval_ms,
                generation_ms=gate_ms,
                chunk_texts=[r.chunk.content for r in retrieval.results],
            )

        # ── Generation ─────────────────────────────────────────────────────
        t1 = time.perf_counter()
        generation = self._generator.generate(retrieval, history=history, model=model)
        generation_ms = (time.perf_counter() - t1) * 1000

        return RAGResponse(
            answer=generation.answer,
            query=question,
            citations=generation.citations,
            retrieval_scores=[r.score for r in retrieval.results],
            chunks_used=retrieval.total,
            model=generation.model,
            retrieval_ms=retrieval_ms,
            generation_ms=generation_ms,
            chunk_texts=[r.chunk.content for r in retrieval.results],
        )

    def __repr__(self) -> str:
        return (
            f"RAGPipeline("
            f"retriever={type(self._retriever).__name__}, "
            f"generator={type(self._generator).__name__}, "
            f"top_k={self._top_k})"
        )
