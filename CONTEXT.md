# Workspace State & Context Memory (CONTEXT.md)

> **Project**: Financial Document Intelligence System (FDIS)  
> **Master Protocol**: `/home/shaikhfardin/templates/instructions.md`  
> **Active Phase**: Phase 6 — Production Deployment, Observability & GTM Complete  
> **Last Updated**: 2026-09-06

---

## 📍 Current Phase & Focus
- **Active Phase**: Production Ready & Fully Verified
- **Status**: Backend (FastAPI 4-Tier) & Frontend (Next.js 16 + React 19 + Tailwind v4 OKLCH) running live.
- **Verification**: End-to-end PDF ingestion, Supabase pgvector retrieval, Groq streaming, interactive citations, and drawer verification completed.

---

## 📋 Features Built & Verified

- [x] **Phase 0**: Research & Disconfirmation Gate approved
- [x] **Phase 1**: Infrastructure reachability verified (Supabase pgvector 0.8.2, Groq qwen3.8-27b, OpenRouter, Resend)
- [x] **Phase 2**: Architecture approved (Approach 3: Pragmatic 4-Tier Clean Architecture)
- [x] **Phase 3**: Single-Source-of-Truth documentation setup complete (`docs/PRD.md`, `docs/architecture.md`, `docs/api-docs.md`, `docs/deployment.md`, `docs/TEST.md`, `AGENTS.md`)
- [x] **Phase 4.1**: Backend core & dependencies setup via `uv` (FastAPI 0.141, PyMuPDF 1.28, sentence-transformers 6.0, Pydantic v2)
- [x] **Phase 4.2**: PyMuPDF extraction with table awareness, memory cleanup (`fitz.TOOLS.store_shrink(100)`), and recursive financial chunking (512 char target, 64 overlap)
- [x] **Phase 4.3**: Supabase pgvector cosine retrieval via optimized `match_chunks` RPC with document B-tree index scan
- [x] **Phase 4.4**: Groq LPU sub-second streaming on `/api/v1/ask/stream` with transparent OpenRouter fallback and inline `[X]` citations
- [x] **Phase 4.5**: Next.js 16 + React 19 + Tailwind CSS v4 OKLCH Frontend with 5 UI states, document drawer, and interactive citation inspector
- [x] **Phase 5**: Multi-lens review, client secret leak audit (`0 secrets exposed`), and live Playwright browser verification

---

## 🐞 Bug Log & Resolutions
- **Issue**: `ivfflat` index filtered query with `document_id = ANY(...)` returned 0 rows due to single-probe cluster partitioning.
  - **Fix**: Updated `match_chunks` stored procedure in Supabase PostgreSQL to use B-tree index scan when filtering by `p_document_ids`. Verified 100% match accuracy.
- **Issue**: `UUID` serialization error in SSE streaming citations payload.
  - **Fix**: Added `mode="json"` to `c.model_dump()` in `src/services/inference.py`.

- **Issue**: Structural Invariant Drift (Playbook Rules & Template Specifications deviation).
  - **Fix**: Researched via Exa AI (`Constraint Decay: The Fragility of LLM Agents in Backend Code Generation`). Updated Master Global Templates (`AGENTS_template.md`, `instructions.md`, `docs/TEST_template.md`, `docs/api-docs_template.md`) with explicit enforcement gates. Created and executed `templates/scripts/verify-playbook.py`.
  - **Refactored**:
    - Backend: Unified response envelopes (`UnifiedResponse[T]`, `ResponseMeta`), RFC 9457 validation errors, live database probe with latency tracking (`/api/v1/health`), SSE client disconnect defense (`request.is_disconnected()`), multi-model fallback array (`models: [...]`).
    - Frontend: State separation (TanStack Query for server state, Zustand `useFDISStore` for UI state), elimination of raw `<button>` in favor of accessible `@/components/ui/button`, `tabular-nums font-mono` for financial numbers, and Skeleton mirror loading states.
  - **Verification**: `python3 /home/shaikhfardin/templates/scripts/verify-playbook.py .` returned **0 violations (PASS)**. `uv run pytest -v` (13/13 PASS). `pnpm run typecheck` (0 errors).
