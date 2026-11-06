# Financial Document Intelligence System

Private PDF report retrieval and question-answering with streamed answers and page-level source citations.

## Current status

Work is on `backend-hardening`, not merged to `main` or deployed. Do not treat a passing unit test, a prompt, or an empty database as proof of production readiness. There is no guaranteed zero-hallucination, latency, uptime or zero-cost claim.

The financial-rag app database was rebuilt with approval on 6 November 2026 using migrations 0001-0003. Verification found empty documents/chunks tables, owner policies, queue functions and UUID document linkage. Auth settings and storage were not changed. New migration 0004 (safe deletion) is source-only and not applied; the new deletion API requires it before deployment. End-to-end login/upload/embedding/answer and two-user live isolation remain unverified.

## Product boundary

- Text-based corporate reports: private upload, processing states, selected-document retrieval, streaming Q&A, page citations and authenticated PDF viewing.
- Scanned/empty and password-protected PDFs are rejected; OCR is not implemented.
- Financial units, reporting periods and source evidence matter. Generated answers require review; this is not investment advice.
- Cross-device conversations, OCR, structured financial extraction and team sharing are future work. Chat history is browser-local and account-scoped, not server persistence.

## Architecture

Next.js (version pinned in frontend/package.json) + React frontend → FastAPI → Supabase Postgres/pgvector and private Storage. Retrieval uses Hugging Face feature extraction. The optional workspace AI flow uses a separate Puter Connect popup and free-model allowlist; backend Groq streaming remains an explicit API route, not an automatic Puter failure fallback. OpenRouter fallback is disabled unless explicitly enabled and configured. Model identifiers in examples are configuration defaults, not current availability or free-usage guarantees.

Queue ingestion runs a worker in the long-running API host. Claims, leases, heartbeat and fenced writes are in Postgres. Vercel's copied API runs inline, not a production durable-worker target. The frontend can run on Vercel and use a separately hosted long-running backend. No infrastructure has been provisioned by this branch.

## Run locally

Use Python 3.12, uv, Node 20 and pnpm 9. Copy backend/.env.example and frontend/.env.example to local environment files, then supply your own service settings. Never commit real environment files. Authentication fails closed outside explicitly configured local debug use.

```sh
cd backend
uv sync --frozen
uv run uvicorn src.api.main:app --reload --port 8000
# in a second terminal
cd frontend
pnpm install --frozen-lockfile
pnpm dev
```

The frontend has Google OAuth UI plus an opt-in Puter AI authorization flow; hosted Google OAuth client/provider/redirect setup remains pending. Email/password + production SMTP is an alternative, not implemented by this change.

## Offline verification

```sh
cd backend && uv run --group dev pytest -q
cd ..
uv run --python 3.12 --with pgserver --with psycopg2-binary python scripts/test_migrations.py
bash scripts/sync-vercel-api.sh --check
cd frontend && node --test tests/*.test.cjs && pnpm typecheck && pnpm build
```

Live tests are skipped unless RUN_LIVE_TESTS=1 is explicitly supplied. They can use provider quota or money. Do not enable them without an isolated test project, service access and approved usage limits. See docs/deployment.md, SECURITY.md and docs/production-readiness.md for limits and release gates.
