"""Factory to build a ready-to-use RAGPipeline from disk or Supabase.

Backend selection mirrors ``retrieval.factory.create_retriever``:

    backend="faiss" (default)
        Loads a local FAISS index from *store_path*.

    backend="supabase"
        Connects to Supabase using env-supplied credentials.
        *store_path* is ignored.
"""

from __future__ import annotations

from pathlib import Path

from financial_rag.generation.groq import GroqGenerator
from financial_rag.pipeline.pipeline import RAGPipeline
from financial_rag.retrieval.factory import create_retriever


def create_pipeline(
    store_path: str | Path = "data/processed/vector_store",
    model: str = "llama-3.1-8b-instant",
    top_k: int = 5,
    score_threshold: float = 0.0,
    use_reranker: bool = False,
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
    reranker_candidates: int = 20,
    use_hybrid: bool = False,
    api_key: str | None = None,
    backend: str = "faiss",
    supabase_url: str = "",
    supabase_key: str = "",
    supabase_table: str = "chunks",
    supabase_rpc: str = "match_chunks",
) -> RAGPipeline:
    """Load a vector store and wire it into a full RAG pipeline.

    Args:
        store_path: Base path to the FAISS index (without extension).
            Ignored when *backend* is ``"supabase"``.
        model: Groq model tag for generation.
            Options: llama-3.1-8b-instant (fast), llama-3.3-70b-versatile (quality).
        top_k: Default number of chunks passed to the generator.
        score_threshold: Minimum cosine similarity to include a chunk.
        use_reranker: If True, adds a cross-encoder reranker after retrieval.
            Not compatible with backend="supabase" + use_hybrid=True.
        reranker_model: HuggingFace model ID for the cross-encoder.
        reranker_candidates: Number of candidates to retrieve for reranking.
        use_hybrid: BM25 + FAISS with Reciprocal Rank Fusion.
            Only supported for backend="faiss".
        api_key: Groq API key.  Reads GROQ_API_KEY env var when None.
        backend: ``"faiss"`` (default) or ``"supabase"``.
        supabase_url: Supabase project URL.  Required when backend="supabase".
        supabase_key: Supabase API key.  Required when backend="supabase".
        supabase_table: Postgres table name (default ``"chunks"``).
        supabase_rpc: Postgres RPC for vector search (default ``"match_chunks"``).

    Returns:
        RAGPipeline ready to answer questions.
    """
    retriever = create_retriever(
        store_path=store_path,
        score_threshold=score_threshold,
        use_reranker=use_reranker,
        reranker_model=reranker_model,
        reranker_candidates=reranker_candidates,
        use_hybrid=use_hybrid,
        backend=backend,
        supabase_url=supabase_url,
        supabase_key=supabase_key,
        supabase_table=supabase_table,
        supabase_rpc=supabase_rpc,
    )
    generator = GroqGenerator(model=model, api_key=api_key)

    return RAGPipeline(
        retriever=retriever, generator=generator, top_k=top_k
    )
