"""Supabase-backed vector store using pgvector for chunk retrieval.

SQL prerequisites (run once in Supabase SQL editor):
------------------------------------------------------
-- 1. Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Chunks table
CREATE TABLE IF NOT EXISTS chunks (
    id           BIGSERIAL PRIMARY KEY,
    content      TEXT        NOT NULL,
    source       TEXT        NOT NULL,
    page         INTEGER     NOT NULL DEFAULT 0,
    chunk_index  INTEGER     NOT NULL DEFAULT 0,
    total_chunks INTEGER     NOT NULL DEFAULT 1,
    metadata     JSONB       NOT NULL DEFAULT '{}',
    embedding    vector(384) NOT NULL
);

-- 3. ANN index (cosine distance)
CREATE INDEX IF NOT EXISTS chunks_embedding_idx
    ON chunks USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- 4. match_chunks RPC
CREATE OR REPLACE FUNCTION match_chunks(
    query_embedding  vector(384),
    match_threshold  float,
    match_count      int
)
RETURNS TABLE (
    id           bigint,
    content      text,
    source       text,
    page         integer,
    chunk_index  integer,
    total_chunks integer,
    metadata     jsonb,
    similarity   float
)
LANGUAGE sql STABLE AS $$
    SELECT
        id, content, source, page, chunk_index, total_chunks, metadata,
        1 - (embedding <=> query_embedding) AS similarity
    FROM chunks
    WHERE 1 - (embedding <=> query_embedding) >= match_threshold
    ORDER BY embedding <=> query_embedding
    LIMIT match_count;
$$;
"""

from __future__ import annotations

from financial_rag.chunking.models import Chunk
from financial_rag.embeddings.base import BaseEmbedder
from financial_rag.retrieval.vector_store import SearchResult


class SupabaseVectorStore:
    """Stores chunk embeddings in Supabase (pgvector) and supports similarity search.

    Drop-in companion to FAISSVectorStore: exposes the same ``add_chunks``,
    ``search``, ``size``, ``is_empty``, and ``chunks`` interface so that
    ``VectorRetriever`` works without changes.

    Requires the ``supabase`` Python package (``pip install supabase``).

    Args:
        supabase_url: Supabase project URL (e.g. https://<ref>.supabase.co).
        supabase_key: Service-role or anon API key.
        table: Postgres table name (default ``"chunks"``).
        rpc_fn: Postgres function used for vector search (default ``"match_chunks"``).
    """

    def __init__(
        self,
        supabase_url: str,
        supabase_key: str,
        table: str = "chunks",
        rpc_fn: str = "match_chunks",
    ) -> None:
        try:
            from supabase import create_client, Client  # type: ignore[import]
            self._client: Client = create_client(supabase_url, supabase_key)
        except ImportError as exc:
            raise ImportError(
                "The 'supabase' package is required for SupabaseVectorStore. "
                "Install it with:  pip install supabase"
            ) from exc

        self._table = table
        self._rpc_fn = rpc_fn
        # Invalidated after every insert so repeated .size calls stay cheap.
        self._size_cache: int | None = None
    # ── Building the store ────────────────────────────────────────────────

    def add_chunks(self, chunks: list[Chunk], embedder: BaseEmbedder) -> None:
        """Embed *chunks* and insert them into the Supabase ``chunks`` table.

        Args:
            chunks: Chunks to index.
            embedder: Must produce 384-dimensional L2-normalised vectors.
        """
        if not chunks:
            return

        texts = [c.content for c in chunks]
        vectors = embedder.embed(texts)  # shape (N, dim), already normalised

        rows = [
            {
                "content": chunk.content,
                "source": chunk.source,
                "page": chunk.page,
                "chunk_index": chunk.chunk_index,
                "total_chunks": chunk.total_chunks,
                "metadata": chunk.metadata,
                "document_id": chunk.metadata.get("document_id"),
                "embedding": vec.tolist(),
            }
            for chunk, vec in zip(chunks, vectors)
        ]

        batch_size = 500
        for i in range(0, len(rows), batch_size):
            batch = rows[i : i + batch_size]
            self._client.table(self._table).insert(batch).execute()
            
        self._size_cache = None  # invalidate count cache

    def clear(self) -> None:
        """Delete ALL rows from the chunks table.

        This is used before a full rebuild to ensure no stale rows remain.
        The operation is a simple DELETE with a always-true filter so that
        the Supabase client does not complain about a missing WHERE clause.
        """
        self._client.table(self._table).delete().neq("id", -1).execute()
        self._size_cache = 0

    def delete_by_document_id(self, document_id: str) -> None:
        """Delete all chunks for a specific document."""
        self._client.table(self._table).delete().eq("metadata->>document_id", document_id).execute()
        self._size_cache = None

    # ── Searching ─────────────────────────────────────────────────────────

    def search(
        self,
        query: str,
        embedder: BaseEmbedder,
        top_k: int = 5,
        score_threshold: float = 0.0,
        document_ids: list[str] | None = None,
    ) -> list[SearchResult]:
        """Find the most relevant chunks via the ``match_chunks`` Postgres RPC.

        Expected RPC signature::

            match_chunks(
                query_embedding  vector(384),
                match_threshold  float,
                match_count      int
            ) RETURNS TABLE (
                id bigint, content text, source text, page int,
                chunk_index int, total_chunks int, metadata jsonb,
                similarity float
            )

        Args:
            query: Natural language question.
            embedder: Same model used during indexing.
            top_k: Maximum number of results to return.
            score_threshold: Minimum cosine similarity in [0, 1].

        Returns:
            List of :class:`SearchResult` ordered by descending similarity.
        """
        query_vec = embedder.embed_query(query)

        rpc_params = {
            "query_embedding": query_vec.tolist(),
            "match_threshold": float(score_threshold),
            "match_count": int(top_k),
        }
        
        if "hybrid" in self._rpc_fn:
            rpc_params["query_text"] = query

        if document_ids is not None:
            rpc_params["p_document_ids"] = document_ids
        else:
            rpc_params["p_document_ids"] = None  # always send to resolve overload ambiguity

        response = self._client.rpc(
            self._rpc_fn,
            rpc_params,
        ).execute()

        rows: list[dict] = response.data or []
        results: list[SearchResult] = []
        for rank, row in enumerate(rows):
            chunk = Chunk(
                content=row["content"],
                source=row["source"],
                page=int(row["page"]),
                chunk_index=int(row["chunk_index"]),
                total_chunks=int(row["total_chunks"]),
                metadata=row.get("metadata") or {},
            )
            results.append(
                SearchResult(chunk=chunk, score=float(row["similarity"]), rank=rank)
            )

        return results

    # ── Properties ────────────────────────────────────────────────────────

    @property
    def chunks(self) -> list[Chunk]:
        """All chunks currently stored (full table scan — use sparingly)."""
        response = (
            self._client.table(self._table)
            .select("content, source, page, chunk_index, total_chunks, metadata")
            .execute()
        )
        return [
            Chunk(
                content=row["content"],
                source=row["source"],
                page=int(row["page"]),
                chunk_index=int(row["chunk_index"]),
                total_chunks=int(row["total_chunks"]),
                metadata=row.get("metadata") or {},
            )
            for row in (response.data or [])
        ]

    @property
    def size(self) -> int:
        """Row count in the table (cached until the next :meth:`add_chunks`)."""
        if self._size_cache is not None:
            return self._size_cache
        response = (
            self._client.table(self._table)
            .select("id", count="exact")
            .execute()
        )
        self._size_cache = response.count or 0
        return self._size_cache

    @property
    def is_empty(self) -> bool:
        return self.size == 0

    def __repr__(self) -> str:
        cached = self._size_cache if self._size_cache is not None else "?"
        return f"SupabaseVectorStore(table={self._table!r}, size={cached})"
