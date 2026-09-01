-- ============================================================
-- Financial RAG Assistant -- Phase 1 Migration
-- PDF Upload & Multi-Document Retrieval
-- ============================================================

-- 1. Add document_id to chunks table (Non-destructive: existing rows get NULL)
ALTER TABLE chunks
ADD COLUMN IF NOT EXISTS document_id TEXT;

-- 2. Create partial index for performance on document-scoped queries
CREATE INDEX IF NOT EXISTS chunks_document_id_idx
ON chunks (document_id)
WHERE document_id IS NOT NULL;

-- 3. Create documents registry table
CREATE TABLE IF NOT EXISTS documents (
    id            UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    filename      TEXT         NOT NULL,
    page_count    INTEGER      NOT NULL DEFAULT 0,
    chunk_count   INTEGER      NOT NULL DEFAULT 0,
    status        TEXT         NOT NULL DEFAULT 'processing',
    error_message TEXT,
    is_sample     BOOLEAN      NOT NULL DEFAULT false,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- 4. Update match_chunks RPC to support p_document_ids filtering
CREATE OR REPLACE FUNCTION match_chunks(
    query_embedding  vector(384),
    match_threshold  float,
    match_count      int,
    p_document_ids   text[] DEFAULT NULL
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
        id,
        content,
        source,
        page,
        chunk_index,
        total_chunks,
        metadata,
        1 - (embedding <=> query_embedding) AS similarity
    FROM  chunks
    WHERE 1 - (embedding <=> query_embedding) >= match_threshold
      AND (
          p_document_ids IS NULL
          OR document_id = ANY(p_document_ids)
      )
    ORDER BY embedding <=> query_embedding
    LIMIT match_count;
$$;

-- 5. Update match_chunks_hybrid RPC to support p_document_ids filtering
CREATE OR REPLACE FUNCTION match_chunks_hybrid(
    query_embedding  vector(384),
    query_text       text,
    match_threshold  float,
    match_count      int,
    p_document_ids   text[] DEFAULT NULL
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
    WITH hybrid_scores AS (
        SELECT
            id,
            content,
            source,
            page,
            chunk_index,
            total_chunks,
            metadata,
            1 - (embedding <=> query_embedding) AS vec_score,
            ts_rank_cd(
                to_tsvector('english', content),
                replace(plainto_tsquery('english', query_text)::text, '&', '|')::tsquery
            ) AS raw_ts_score
        FROM chunks
        WHERE 1 - (embedding <=> query_embedding) >= (match_threshold - 0.2)
          AND (
              p_document_ids IS NULL
              OR document_id = ANY(p_document_ids)
          )
    )
    SELECT
        id,
        content,
        source,
        page,
        chunk_index,
        total_chunks,
        metadata,
        (vec_score * 0.7) + ((raw_ts_score / (raw_ts_score + 1.0)) * 0.3) AS similarity
    FROM hybrid_scores
    ORDER BY similarity DESC
    LIMIT match_count;
$$;
