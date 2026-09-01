"""Factory to build a VectorRetriever from a saved index or Supabase table.

Backend selection
-----------------
backend="faiss" (default)
    Loads a local FAISS index from *store_path*.  All existing callers continue
    to work unchanged — this is purely additive.

backend="supabase"
    Connects to a Supabase project using *supabase_url* / *supabase_key* and
    wraps the ``chunks`` table + ``match_chunks`` RPC in a SupabaseVectorStore.
    *store_path* is ignored for this backend.
"""

from __future__ import annotations

from pathlib import Path

from financial_rag.embeddings.base import BaseEmbedder
from financial_rag.retrieval.base import BaseRetriever
from financial_rag.retrieval.hybrid import HybridRetriever
from financial_rag.retrieval.retriever import VectorRetriever
from financial_rag.retrieval.vector_store import FAISSVectorStore

_VALID_BACKENDS = {"faiss", "supabase"}


def create_retriever(
    store_path: str | Path = "data/processed/vector_store",
    embedder: BaseEmbedder | None = None,
    score_threshold: float = 0.0,
    use_reranker: bool = False,
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
    reranker_candidates: int = 20,
    use_hybrid: bool = False,
    backend: str = "faiss",
    supabase_url: str = "",
    supabase_key: str = "",
    supabase_table: str = "chunks",
    supabase_rpc: str = "match_chunks",
) -> BaseRetriever:
    """Build a retriever backed by either FAISS (local) or Supabase (pgvector).

    Args:
        store_path: Base path to the FAISS index (no extension).
            Ignored when *backend* is ``"supabase"``.
        embedder: Pre-built embedder.  Defaults to all-MiniLM-L6-v2 when None.
        score_threshold: Minimum cosine similarity for a result.
        use_reranker: If True, adds a cross-encoder reranker.
        reranker_model: HuggingFace model ID for the cross-encoder.
        reranker_candidates: Number of candidates to retrieve for reranking.
        use_hybrid: Combine BM25 + vector search via Reciprocal Rank Fusion.
            Only supported for ``backend="faiss"``; raises ``ValueError`` otherwise.
        backend: ``"faiss"`` (default) or ``"supabase"``.
        supabase_url: Supabase project URL — required when backend="supabase".
        supabase_key: Supabase API key — required when backend="supabase".
        supabase_table: Postgres table name (default ``"chunks"``).
        supabase_rpc: Postgres RPC function for vector search (default ``"match_chunks"``).

    Returns:
        Ready-to-query :class:`VectorRetriever` or :class:`HybridRetriever`.

    Raises:
        ValueError: Unknown backend, or use_hybrid=True with Supabase backend.
    """
    if backend not in _VALID_BACKENDS:
        raise ValueError(
            f"Unknown backend {backend!r}. Valid options: {sorted(_VALID_BACKENDS)}"
        )

    if use_hybrid and backend != "faiss":
        raise ValueError(
            "use_hybrid=True is only supported with backend='faiss'. "
            "Supabase hybrid retrieval is not yet implemented."
        )

    # ── Resolve embedder ──────────────────────────────────────────────────
    if embedder is None:
        from financial_rag.embeddings.sentence_transformer import SentenceTransformerEmbedder
        embedder = SentenceTransformerEmbedder()

    # ── Resolve reranker ──────────────────────────────────────────────────
    reranker = None
    if use_reranker:
        from financial_rag.retrieval.reranker import CrossEncoderReranker
        reranker = CrossEncoderReranker(model=reranker_model)

    # ── Build the vector store ────────────────────────────────────────────
    if backend == "supabase":
        from financial_rag.retrieval.supabase_vector_store import SupabaseVectorStore
        store = SupabaseVectorStore(
            supabase_url=supabase_url,
            supabase_key=supabase_key,
            table=supabase_table,
            rpc_fn=supabase_rpc,
        )
        return VectorRetriever(
            store=store, 
            embedder=embedder, 
            score_threshold=score_threshold,
            reranker=reranker,
            reranker_candidates=reranker_candidates,
        )

    # backend == "faiss"
    store = FAISSVectorStore.load(store_path)

    if use_hybrid:
        return HybridRetriever(
            store=store, 
            embedder=embedder, 
            score_threshold=score_threshold,
        )

    return VectorRetriever(
        store=store, 
        embedder=embedder, 
        score_threshold=score_threshold,
        reranker=reranker,
        reranker_candidates=reranker_candidates,
    )
