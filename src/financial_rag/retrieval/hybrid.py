"""Hybrid BM25 + FAISS retriever with Reciprocal Rank Fusion.

Why hybrid search:
- FAISS (dense) captures semantic similarity — good for paraphrased questions.
- BM25 (sparse) captures exact keyword matches — good for proper nouns, figures,
  and Spanish-specific terms that embeddings may not encode well.
- Reciprocal Rank Fusion (RRF) combines both rankings without needing to
  normalize scores across different scales.

RRF formula:  score(d) = Σ  1 / (k + rank(d, system_i))
              where k=60 is the standard constant that dampens high-rank outliers.
"""

from dataclasses import dataclass

from financial_rag.embeddings.base import BaseEmbedder
from financial_rag.retrieval.base import BaseRetriever
from financial_rag.retrieval.models import RetrievalResult
from financial_rag.retrieval.vector_store import FAISSVectorStore, SearchResult

_RRF_K = 60  # standard RRF constant


@dataclass
class _BM25Index:
    """Thin wrapper around rank_bm25.BM25Okapi tied to the chunk list."""

    chunks: list  # list[Chunk] — parallel to the BM25 corpus
    _bm25: object = None

    def __post_init__(self) -> None:
        if not self.chunks:
            self._bm25 = None
            return
        from rank_bm25 import BM25Okapi
        tokenized = [self._tokenize(c.content) for c in self.chunks]
        self._bm25 = BM25Okapi(tokenized)

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return text.lower().split()

    def query(self, text: str, top_k: int) -> list[tuple[int, float]]:
        """Return (chunk_index, bm25_score) for the top_k chunks."""
        if self._bm25 is None:
            return []
        scores = self._bm25.get_scores(self._tokenize(text))
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        return ranked[:top_k]


class HybridRetriever(BaseRetriever):
    """Two-stage retriever: BM25 + FAISS fused with Reciprocal Rank Fusion.

    Args:
        store: Loaded FAISSVectorStore (also the source of the BM25 corpus).
        embedder: Same model used to build the FAISS index.
        score_threshold: Minimum FAISS cosine similarity (applied before fusion).
        rrf_k: RRF constant (default 60 — standard value from the original paper).
    """

    def __init__(
        self,
        store: FAISSVectorStore,
        embedder: BaseEmbedder,
        score_threshold: float = 0.0,
        rrf_k: int = _RRF_K,
    ) -> None:
        self._store = store
        self._embedder = embedder
        self._score_threshold = score_threshold
        self._rrf_k = rrf_k
        self._bm25 = _BM25Index(chunks=store.chunks)

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        source_filter: str | None = None,
    ) -> RetrievalResult:
        # Expand candidate pool when filtering — many candidates will be discarded,
        # so we need a larger initial set to still return top_k after the filter.
        candidate_k = top_k * 3 if not source_filter else min(top_k * 10, self._store.size)

        # ── Dense (FAISS) retrieval ───────────────────────────────────────
        faiss_results: list[SearchResult] = self._store.search(
            query=query,
            embedder=self._embedder,
            top_k=candidate_k,
            score_threshold=self._score_threshold,
        )

        # ── Sparse (BM25) retrieval ───────────────────────────────────────
        bm25_hits = self._bm25.query(query, top_k=candidate_k)

        # ── Reciprocal Rank Fusion ────────────────────────────────────────
        # Key: (source, chunk_index) — unique per store because each document's
        # splitter never repeats chunk_index within that document.
        # Using chunk_index alone would collide across documents (both start at 0).
        ChunkKey = tuple  # (source: str, chunk_index: int) — unique per document
        rrf_scores: dict[tuple, float] = {}

        for rank, sr in enumerate(faiss_results):
            key: tuple = (sr.chunk.source, sr.chunk.chunk_index)
            rrf_scores[key] = rrf_scores.get(key, 0.0) + 1.0 / (self._rrf_k + rank)

        for rank, (chunk_pos, _) in enumerate(bm25_hits):
            bm25_chunk = self._bm25.chunks[chunk_pos]
            key = (bm25_chunk.source, bm25_chunk.chunk_index)
            rrf_scores[key] = rrf_scores.get(key, 0.0) + 1.0 / (self._rrf_k + rank)

        # Build lookups using the same compound key
        faiss_lookup: dict[ChunkKey, SearchResult] = {
            (sr.chunk.source, sr.chunk.chunk_index): sr for sr in faiss_results
        }
        bm25_lookup: dict[ChunkKey, object] = {
            (self._bm25.chunks[pos].source, self._bm25.chunks[pos].chunk_index): self._bm25.chunks[pos]
            for pos, _ in bm25_hits
        }

        # Walk all candidates sorted by RRF score, applying source_filter as we go.
        # This ensures we collect up to top_k matching results even when the filter
        # discards many of the top-ranked candidates.
        sorted_keys = sorted(rrf_scores, key=lambda k: rrf_scores[k], reverse=True)

        results: list[SearchResult] = []
        for key in sorted_keys:
            if len(results) >= top_k:
                break
            chunk = (
                faiss_lookup[key].chunk
                if key in faiss_lookup
                else bm25_lookup[key]
            )
            if source_filter and source_filter.lower() not in chunk.source.lower():
                continue
            results.append(SearchResult(chunk=chunk, score=rrf_scores[key], rank=len(results)))

        return RetrievalResult(query=query, results=results)

    @property
    def store_size(self) -> int:
        return self._store.size

    def __repr__(self) -> str:
        return (
            f"HybridRetriever(store_size={self.store_size}, "
            f"embedder={type(self._embedder).__name__}, "
            f"rrf_k={self._rrf_k})"
        )
