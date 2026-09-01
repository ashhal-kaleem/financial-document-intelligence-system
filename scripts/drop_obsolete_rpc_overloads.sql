-- ============================================================
-- Financial RAG Assistant — RPC Overload Cleanup
-- Drops the obsolete 4-argument versions of match_chunks and
-- match_chunks_hybrid that predate the Phase 1 migration.
--
-- The 5-argument versions (with p_document_ids text[] DEFAULT NULL)
-- are the ONLY intended signatures and must NOT be dropped.
--
-- Safe to run multiple times (DROP IF EXISTS).
-- ============================================================

-- Drop obsolete 4-argument match_chunks_hybrid
-- Signature: (vector(384), text, float, int)
DROP FUNCTION IF EXISTS public.match_chunks_hybrid(
    extensions.vector,
    text,
    double precision,
    integer
);

-- Drop obsolete 4-argument match_chunks
-- Signature: (vector(384), float, int)
DROP FUNCTION IF EXISTS public.match_chunks(
    extensions.vector,
    double precision,
    integer
);

-- ============================================================
-- After running this script, verify with:
--
--   SELECT proname, pg_get_function_identity_arguments(oid)
--   FROM pg_proc
--   JOIN pg_namespace ON pronamespace = pg_namespace.oid
--   WHERE nspname = 'public'
--     AND proname IN ('match_chunks_hybrid', 'match_chunks');
--
-- Expected: exactly 2 rows, both with p_document_ids => text[]
-- ============================================================
