-- ============================================================
-- Financial RAG Assistant -- Supabase schema setup
-- Run this ONCE in the Supabase SQL Editor:
--   Dashboard > your project > SQL Editor > New query
-- ============================================================

-- 1. Enable pgvector extension (idempotent)
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Chunks table (384-dim vectors to match all-MiniLM-L6-v2)
CREATE TABLE IF NOT EXISTS chunks (
    id           BIGSERIAL    PRIMARY KEY,
    content      TEXT         NOT NULL,
    source       TEXT         NOT NULL,
    page         INTEGER      NOT NULL DEFAULT 0,
    chunk_index  INTEGER      NOT NULL DEFAULT 0,
    total_chunks INTEGER      NOT NULL DEFAULT 1,
    metadata     JSONB        NOT NULL DEFAULT '{}',
    embedding    vector(384)  NOT NULL
);

-- 3. IVFFlat ANN index on cosine distance
--    (lists=100 is appropriate for up to ~1M rows)
CREATE INDEX IF NOT EXISTS chunks_embedding_idx
    ON chunks
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- 4. Similarity-search RPC used by SupabaseVectorStore.search()
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
    ORDER BY embedding <=> query_embedding
    LIMIT match_count;
$$;

-- 4b. Hybrid-search RPC combining vector similarity and full-text search
--     NOTE: uses 'english' text config — documents are HBL/ABL English annual reports.
CREATE OR REPLACE FUNCTION match_chunks_hybrid(
    query_embedding  vector(384),
    query_text       text,
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
            -- English text config — correct for HBL/ABL annual reports.
            -- OR-query so partial keyword matches (e.g. "ROE", "return") all score.
            ts_rank_cd(
                to_tsvector('english', content),
                replace(plainto_tsquery('english', query_text)::text, '&', '|')::tsquery
            ) AS raw_ts_score
        FROM chunks
        WHERE 1 - (embedding <=> query_embedding) >= (match_threshold - 0.2)
    )
    SELECT
        id,
        content,
        source,
        page,
        chunk_index,
        total_chunks,
        metadata,
        -- Normalize ts_rank using rank / (rank + 1) to bound it to [0, 1)
        (vec_score * 0.7) + ((raw_ts_score / (raw_ts_score + 1.0)) * 0.3) AS similarity
    FROM hybrid_scores
    ORDER BY similarity DESC
    LIMIT match_count;
$$;

-- 5. Row-Level Security
--    The sb_sec* (service-role) key bypasses RLS automatically in Supabase,
--    so this is belt-and-suspenders only.
ALTER TABLE chunks ENABLE ROW LEVEL SECURITY;

-- Idempotent policy creation (IF NOT EXISTS not available until PG 17)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename  = 'chunks'
          AND policyname = 'service role full access'
    ) THEN
        CREATE POLICY "service role full access"
            ON chunks
            FOR ALL
            TO service_role
            USING (true)
            WITH CHECK (true);
    END IF;
END $$;
