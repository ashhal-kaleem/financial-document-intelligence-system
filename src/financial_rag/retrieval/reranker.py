"""Cross-encoder re-ranking for retrieved chunks.

Pattern: retrieve broad (top_k * 3 from FAISS), rerank with a cross-encoder,
return the top_k most relevant by semantic similarity to the query.

Why: FAISS bi-encoder scores measure how close embeddings are in vector space,
which captures general semantic similarity but misses fine-grained relevance.
A cross-encoder reads (query, chunk) jointly and scores them with full attention,
catching nuances the bi-encoder misses — at the cost of being O(n) per query
vs. O(1) ANN lookup.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from financial_rag.retrieval.vector_store import SearchResult


class BaseReranker(ABC):
    """Contract for re-ranking components."""

    @abstractmethod
    def rerank(self, query: str, results: list[SearchResult], top_k: int) -> list[SearchResult]:
        """Re-score and sort results by relevance to query, return top_k.

        Args:
            query: The original user question.
            results: Candidate results from a first-stage retriever.
            top_k: Number of results to return after re-ranking.

        Returns:
            Sorted list of at most top_k SearchResult objects, best first.
            Rank fields are updated to reflect the new ordering.
        """
        ...


class CrossEncoderReranker(BaseReranker):
    """Re-ranks retrieved chunks using a cross-encoder model.

    Args:
        model: HuggingFace model ID. Defaults to a fast, high-quality MS MARCO model.
    """

    def __init__(self, model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2") -> None:
        from sentence_transformers import CrossEncoder
        self._model_name = model
        self._encoder = CrossEncoder(model)

    def rerank(self, query: str, results: list[SearchResult], top_k: int) -> list[SearchResult]:
        if not results:
            return []

        pairs = [(query, r.chunk.content) for r in results]
        scores = self._encoder.predict(pairs)

        reranked = sorted(
            zip(scores, results),
            key=lambda x: float(x[0]),
            reverse=True,
        )

        return [
            SearchResult(chunk=r.chunk, score=float(score), rank=i)
            for i, (score, r) in enumerate(reranked[:top_k])
        ]

    def __repr__(self) -> str:
        return f"CrossEncoderReranker(model={self._model_name!r})"


class MockReranker(BaseReranker):
    """No-op reranker for tests — returns candidates unchanged."""

    def rerank(self, query: str, results: list[SearchResult], top_k: int) -> list[SearchResult]:
        return [
            SearchResult(chunk=r.chunk, score=r.score, rank=i)
            for i, r in enumerate(results[:top_k])
        ]
