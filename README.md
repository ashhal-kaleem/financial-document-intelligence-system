# Financial Document Intelligence System

Private PDF report retrieval and question-answering with streamed answers and page-level source citations.

## Current status

Source is merged to main. Frontend is deployed on Vercel Hobby and backend on Render Free. Deployment is not production certification: Google sign-in setup, private documents bucket, hosted migrations 0004/0005 and real end-to-end acceptance remain pending. No guaranteed zero-hallucination, latency, uptime or zero-cost claim.

Hosted app schema was checked after migrations 0001-0003. Source contains safe-delete 0004 and strict owned-read 0005; neither has been applied hosted. API filters owned/non-sample documents, but direct hosted read policies still need the approved migration. Real login/upload/embedding/answer/PDF/delete and two-user isolation remain unverified.

## Product boundary

- Text-based corporate reports: private upload, processing states, selected-document retrieval, streaming Q&A, page citations and authenticated PDF viewing.
- Scanned/empty and password-protected PDFs are rejected; OCR is not implemented.
- Financial units, reporting periods and source evidence matter. Generated answers require review; this is not investment advice.
- Cross-device conversations, OCR, structured financial extraction and team sharing are future work. Chat history is browser-local and account-scoped, not server persistence.

## Architecture

Next.js (version pinned in frontend/package.json) + React frontend → FastAPI → Supabase Postgres/pgvector and private Storage. Retrieval uses Hugging Face feature extraction. The optional workspace AI flow uses a separate Puter Connect popup and free-model allowlist; backend Groq streaming remains an explicit API route, not an automatic Puter failure fallback. OpenRouter fallback is disabled unless explicitly enabled and configured. Model identifiers in examples are configuration defaults, not current availability or free-usage guarantees.

Queue ingestion runs a worker in the long-running API host. Claims, leases, heartbeat and fenced writes are in Postgres. Vercel hosts the frontend only. Render hosts the single FastAPI backend and durable queue worker. The existing frontend/backend deployments are active; hosted data/auth configuration is separately controlled.

## Run locally

Supported build checks use Python 3.11/3.12 and Node 20/22 with pnpm 9. The production backend Dockerfile uses Python 3.11; the frontend host uses Node 22. Copy backend/.env.example and frontend/.env.example to local environment files, then supply your own service settings. Never commit real environment files. Authentication fails closed outside explicitly configured local debug use.

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
cd frontend && node --test tests/*.test.cjs && pnpm typecheck && pnpm build
```

Live tests are skipped unless RUN_LIVE_TESTS=1 is explicitly supplied. They can use provider quota or money. Do not enable them without an isolated test project, service access and approved usage limits. See docs/deployment.md, SECURITY.md and docs/production-readiness.md for limits and release gates.
