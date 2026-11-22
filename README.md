# Financial Document Intelligence System

A private financial-document RAG app: upload a corporate PDF, retrieve relevant passages, ask a question and inspect page-level evidence. The product idea has not changed.

## Current architecture

- Next.js/React frontend and FastAPI backend on separate Vercel Hobby projects.
- Supabase Auth, private PDF storage and Postgres/pgvector.
- Public `sentence-transformers/all-MiniLM-L6-v2` weights downloaded from a fixed HF revision at build time and run locally on backend CPU with ONNX Runtime.
- No hosted HF embedding API, HF token or Cloudflare integration.
- Answers are generated server-side on the Groq free plan (pinned `openai/gpt-oss-120b`). The key stays on the server; only the question and retrieved passages of the caller's own PDFs are sent. Daily free quotas apply; there is no paid fallback.

The browser uploads directly to private Supabase storage with an object-scoped signed URL. The backend checks the stored file and processes it inline on Vercel. The app accepts PDFs up to 4 MiB in the current deployment; the bucket has a separate admission limit. Text-only PDFs are supported; scanned/empty and password-protected PDFs are rejected. OCR, structured extraction and financial-analysis dashboards are not implemented.

Local vectors use a pinned model/profile, masked mean pooling, L2 normalization and token-aware splits with a 256-wordpiece ceiling. Missing/corrupt assets fail closed. Existing vectors are not silently mixed or re-indexed. Table extraction and language-model answers still need financial review.

## Status and evidence

The MiniLM backend has been built and deployed, and a public financial-statement PDF page has reached ready through the real signed-upload flow. Owner-scoped retrieval and negative cross-user access checks have live evidence. Exact test scope, narrow retrieval results, known Hinglish miss and the answer-generation evidence are in [production-readiness](docs/production-readiness.md).

Do not equate code pushed, preview built, production deployed, retrieval tested and a correct final answer. Free personal hosting is not a commercial uptime or unlimited-free guarantee. No login is required: every tab gets a fresh private guest session (Supabase anonymous sign-in in tab-scoped storage); closing the tab ends access, and any PDFs left behind are deleted automatically within about a day. The former Render service remains suspended for rollback.

## Run locally

Use Python 3.11/3.12 and pnpm 9, matching CI and the lockfile. Copy the backend/frontend `.env.example` files to local environment files and supply your own service settings. Never commit secrets.

```sh
cd backend
uv sync --frozen
uv run python scripts/fetch_embedding_model.py
uv run uvicorn src.api.main:app --reload --port 8000
# In another terminal, from the repo root:
cd frontend
pnpm install --frozen-lockfile
pnpm dev
```

The model downloader needs public network access only at build/setup time. Runtime embedding requests never download weights or send PDF text to HF inference. Generated model files are ignored by Git and explicitly bundled in the backend function. Model attribution/license is in `backend/licenses/`.

## Verification and project map

```sh
cd backend && uv run pytest -q
cd ../frontend && node --test tests/*.test.cjs && pnpm typecheck && pnpm build
```

Download/verify model assets before backend tests. Existing live suites remain opt-in, not automatic authority to spend quota or write hosted data. The synthetic PDF/financial seed are test fixtures, not accuracy evidence or private uploaded reports.

- [Architecture](docs/architecture.md): retrieval, ownership, local embeddings, guest sessions and the Groq answer boundary.
- [Deployment](docs/deployment.md): setup, resource limits, data and rollout checks.
- [API](docs/api-docs.md): supported routes and response boundaries.
- [Tests](docs/TEST.md): test map and evidence rules.
- [Readiness](docs/production-readiness.md): completed, live-tested and still open.
- [Product idea](PROJECT_IDEA_FDIS.md) and [PRD](docs/PRD.md): unchanged purpose and behavior.

Updating project notes never authorizes deleting app documents, source history, test fixtures, model assets or database schema. Re-indexing, destructive changes, new data processors and paid services need their own authority.
