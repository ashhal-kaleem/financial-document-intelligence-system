"""Vector similarity retriever — works with FAISSVectorStore or SupabaseVectorStore."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

# Expand financial acronyms before embedding so that all-MiniLM-L6-v2 finds
# semantically close chunks even when the query is a bare abbreviation.
#
# Each entry: acronym -> full human-readable form (no acronym suffix).
# _expand_query() works bi-directionally:
#   - acronym present, full form absent  → prepend full form before acronym
#   - full form present, acronym absent  → append acronym after the sentence
_ACRONYM_MAP: dict[str, str] = {
    "ROE":   "return on equity",
    "ROA":   "return on assets",
    "NIM":   "net interest margin",
    "NPL":   "non-performing loans",
    "CAR":   "capital adequacy ratio",
    "CET1":  "common equity tier 1",
    "EPS":   "earnings per share",
    "P/E":   "price to earnings ratio",
    "CASA":  "current account savings account",
    "PAT":   "profit after tax",
    "PBT":   "profit before tax",
    "RWA":   "risk weighted assets",
    "LDR":   "loan to deposit ratio",
    "NPA":   "non-performing assets",
    "EBITDA": "earnings before interest taxes depreciation amortization",
}


def _expand_query(query: str) -> str:
    """Bi-directionally expand financial acronyms in *query*.

    Two rules applied per acronym:
    1. Acronym present, full form absent  → replace acronym with
       "<full form> <ACRONYM>" so the embedding sees both representations.
    2. Full form present, acronym absent  → append " <ACRONYM>" to the
       end of the query so BM25 also fires on the short token.

    Whole-word matches only (won't mangle 'ROE' inside 'ROEBERT').
    Idempotent: running twice produces the same result.
    """
    import re
    result = query
    lower = query.lower()
    tail_acronyms: list[str] = []  # acronyms to append after all substitutions

    for acronym, full_form in _ACRONYM_MAP.items():
        acronym_present  = bool(re.search(rf"\b{re.escape(acronym)}\b", result))
        full_form_present = full_form.lower() in lower

        if acronym_present and not full_form_present:
            # Case 1: bare acronym → replace with "<full form> <ACRONYM>"
            result = re.sub(
                rf"\b{re.escape(acronym)}\b",
                f"{full_form} {acronym}",
                result,
            )
        elif full_form_present and not acronym_present:
            # Case 2: full form already there → schedule acronym to append
            tail_acronyms.append(acronym)
        # Both present or neither present → nothing to do

    if tail_acronyms:
        result = result.rstrip() + " " + " ".join(tail_acronyms)

    return result

from financial_rag.embeddings.base import BaseEmbedder
from financial_rag.retrieval.base import BaseRetriever
from financial_rag.retrieval.models import RetrievalResult
from financial_rag.retrieval.reranker import BaseReranker
from financial_rag.retrieval.vector_store import FAISSVectorStore, SearchResult

if TYPE_CHECKING:
    from financial_rag.retrieval.supabase_vector_store import SupabaseVectorStore

# Either backend satisfies the duck-typed interface (add_chunks / search / size).
AnyVectorStore = Union[FAISSVectorStore, "SupabaseVectorStore"]


class VectorRetriever(BaseRetriever):
    """Retrieves chunks from a vector store using cosine similarity.

    Works with both :class:`FAISSVectorStore` and
    :class:`SupabaseVectorStore` — any object that exposes
    ``search(query, embedder, top_k, score_threshold) -> list[SearchResult]``
    and a ``size`` property.

    Args:
        store: Pre-built vector store (FAISS or Supabase).
        embedder: Must be the same model used to build the store.
        score_threshold: Minimum cosine similarity to include a result.
        reranker: Optional cross-encoder reranker.
        reranker_candidates: Number of candidates to fetch before reranking.
    """

    def __init__(
        self,
        store: AnyVectorStore,
        embedder: BaseEmbedder,
        score_threshold: float = 0.0,
        reranker: BaseReranker | None = None,
        reranker_candidates: int = 20,
    ) -> None:
        self._store = store
        self._embedder = embedder
        self._score_threshold = score_threshold
        self._reranker = reranker
        self._reranker_candidates = reranker_candidates

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        source_filter: str | None = None,
        document_ids: list[str] | None = None,
    ) -> RetrievalResult:
        """Find the most relevant chunks for a query.

        Args:
            query: Natural language question.
            top_k: Maximum number of results to return.
            source_filter: If set, only return chunks whose source path contains
                this string (case-insensitive). Useful for restricting to a
                specific bank: "interbank", "scotiabank", etc.

        Returns:
            RetrievalResult with ranked chunks.
        """
        # Expand acronyms to improve dense embedding similarity for short queries.
        expanded_query = _expand_query(query)

        # If reranking, we want to start with a larger candidate pool.
        candidate_k = max(top_k, self._reranker_candidates) if self._reranker else top_k

        # Over-fetch when filtering so we still get candidate_k after dropping results.
        fetch_k = candidate_k * 3 if source_filter else candidate_k

        raw: list[SearchResult] = self._store.search(
            query=expanded_query,
            embedder=self._embedder,
            top_k=fetch_k,
            score_threshold=self._score_threshold,
            document_ids=document_ids,
        )

        if source_filter:
            raw = [
                r for r in raw
                if source_filter.lower() in r.chunk.source.lower()
            ]

        filtered = raw[:candidate_k]

        if self._reranker and filtered:
            # We pass the original query to the reranker, NOT the expanded one,
            # so the cross-encoder sees exactly what the user asked.
            filtered = self._reranker.rerank(query, filtered, top_k=top_k)
        else:
            filtered = filtered[:top_k]

        # Re-number ranks after filtering (gaps would confuse downstream code).
        for new_rank, result in enumerate(filtered):
            result.rank = new_rank

        return RetrievalResult(query=query, results=filtered)  # original query, not expanded

    @property
    def store_size(self) -> int:
        return self._store.size

    def __repr__(self) -> str:
        reranker_repr = type(self._reranker).__name__ if self._reranker else "None"
        return (
            f"VectorRetriever(store_size={self.store_size}, "
            f"embedder={type(self._embedder).__name__}, "
            f"score_threshold={self._score_threshold}, "
            f"reranker={reranker_repr})"
        )
