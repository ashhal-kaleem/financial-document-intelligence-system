# Deployment & Production Runbook — Financial Document Intelligence System (FDIS)

> **Status**: Approved  
> **Master Protocol**: `/home/shaikhfardin/templates/instructions.md`  
> **Last Updated**: 2026-09-06

---

## 1. Environment Architecture

- **Frontend**: Next.js 16 (App Router) on Vercel or Docker container.
- **Backend API**: FastAPI asynchronous server running via Uvicorn.
- **Vector Database**: Supabase PostgreSQL 17.6 with `pgvector 0.8.2` (Mumbai `ap-south-1`).
- **Object Storage**: Supabase Storage (`documents` bucket).
- **Inference Engines**: Groq LPU (`qwen/qwen3.8-27b`) with OpenRouter transparent fallback.

---

## 2. Environment Variables & Secret Configuration

### Backend (`backend/.env.local` / Environment)
```env
SUPABASE_URL=https://aluzqooagiymysssnhkg.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
SUPABASE_STORAGE_BUCKET=documents
GROQ_API_KEY=your_groq_key
GROQ_MODEL=qwen/qwen3.8-27b
OPENROUTER_API_KEY=your_openrouter_key
OPENROUTER_DEFAULT_MODEL=liquid/lfm-2.5-2.6b:free
RESEND_API_KEY=your_resend_key
PORT=8000
```

### Frontend (`frontend/.env.local` / Environment)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## 3. Local Development Runbook

### Backend (Python via `uv`)
```bash
cd backend
uv sync
uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend (Next.js via `pnpm`)
```bash
cd frontend
pnpm install
pnpm dev
```

---

## 4. Pre-Flight Production Checklist & Audit

- [ ] Run backend tests: `cd backend && uv run pytest -v`
- [ ] Run frontend typecheck: `cd frontend && pnpm run typecheck`
- [ ] Client Secret Leak Audit:
  ```bash
  grep -rn "API_KEY\|SERVICE_ROLE\|SECRET" frontend/src/ 2>/dev/null | grep -v "NEXT_PUBLIC_"
  ```
  Ensure zero private backend secrets exist in frontend client code.

## Production hardening notes (backend-hardening branch)

**Order matters. Do not deploy this branch before the database steps below.**

1. Database (Supabase SQL editor or CLI), reviewed by a person, never auto-applied:
   - `supabase/migrations/0001_schema.sql` is reconstructed from the code, not exported from the live project. Diff it against the live schema first. It is idempotent, but treat it as a reference, not the source of truth.
   - `0002_document_owner.sql` adds `owner_id`, turns on RLS. Existing rows have no owner and stay hidden (unless `is_sample`). Assigning old documents to a user is a manual, reviewed `update`; nothing does it automatically.
   - `0003_ingestion_queue.sql` adds the job queue columns and the `claim_next_document` and `fail_stale_documents` functions (service role only). Required before `INGESTION_MODE=queue`.
   - `python scripts/test_migrations.py` runs all three against a throwaway local Postgres with pgvector. It proves the SQL behaves as written; it does not prove it matches the live database.
2. Supabase Auth: enable the Google provider and add the frontend URL to the redirect list. Keep the storage bucket private.
3. Backend env: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `ALLOWED_ORIGINS` (JSON list with the frontend URL), `GROQ_API_KEY`, `HF_TOKEN`, optional `OPENROUTER_API_KEY`.
4. Frontend env: `NEXT_PUBLIC_API_URL` (the backend `/api/v1` URL), `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`. There is no built-in fallback project: without these, sign-in is off.

**Ingestion modes.**
- `INGESTION_MODE=inline` (default): the upload request does the whole job (parse, embed, store) and returns 201 when done. Large filings can hit request or proxy timeouts here, so inline is for local use, tests and small files.
- `INGESTION_MODE=queue`: upload stores the PDF and a `queued` row and returns 202. A worker loop inside the API process claims jobs from Postgres and processes them. This needs a **long-running host** (the Render service in `render.yaml` is one). Apply migration 0003 first.
- **Vercel is not a supported production target for queue mode.** On Vercel, `INGESTION_MODE=queue` is ignored and uploads run inline inside the serverless function, with the same timeout risk as inline mode. The copy in `frontend/api` exists so the app can run on Vercel; it is not a durable-ingestion deployment, and nothing here claims serverless production readiness. For production, run the backend on the long-running host and point `NEXT_PUBLIC_API_URL` at it.

**Queue semantics (lease, retry, fencing).**
- A claim sets `status=processing`, `claimed_at=now()` and increments `attempts`. `attempts` is the worker's fencing token.
- A live worker sends a heartbeat every 60 seconds that refreshes `claimed_at`. The 10 minute lease only expires if the worker has really stopped (crash, restart), not because a job is slow.
- If a lease does expire, another worker re-claims the job (`attempts` + 1) up to 3 attempts, then the job becomes `error`.
- Every worker write (clear chunks, insert chunks, finish, heartbeat) is a database function that checks `attempts` under a row lock. A worker that lost its lease gets `false` back, stops, and writes nothing. So two workers can run the same job briefly, but only the latest claim can change chunks or status. Chunks are cleared and rewritten fenced, so retries do not duplicate chunks.
- Known limit: a stalled old worker can waste compute (embedding calls) until its next write is rejected. Embedding calls may be billed even if the result is discarded.
- Not verified against live Supabase. Tested on a local Postgres (`scripts/test_migrations.py`) and with fakes.

**Vercel copy.** `frontend/api/src` is a copy of `backend/src`. Run `scripts/sync-vercel-api.sh` after backend changes; CI checks it.

**Dual route mounting** (`/api/v1/...` and `/...`) is left in place. It could not be verified whether the current Vercel rewrite or any deployed client relies on the root paths, so removing it is a separate change to make after checking the live deployment.
