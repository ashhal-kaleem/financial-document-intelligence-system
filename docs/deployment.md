# Deployment runbook

Status: not deployed from backend-hardening. Last revised 6 November 2026. This is a procedure for a reviewed release, not permission to provision or spend.

## Architecture

- Frontend: Next.js on Vercel, version pinned in frontend/package.json.
- Backend: FastAPI on Render with queue ingestion.
- Data: Supabase Postgres/pgvector, Auth and private Storage.
- Inference: configured Groq model; OpenRouter fallback is explicit opt-in and never joins a partial primary answer. Configured keys do not prove provider availability.

## Before setup

1. Review migrations against the actual target. On 6 November 2026 the financial-rag app schema was rebuilt with approval using 0001-0003. Empty tables, app functions/grants and owner policies were checked live. This does not grant permission for another rebuild or destructive migration. Other projects may have incompatible drift.
2. Resolve the login route: existing UI is Google OAuth. Enabling it requires a Google Cloud client and Supabase provider/redirect settings. Email/password needs UI plus production SMTP for arbitrary signups. Neither route is verified working here. Ask before hosted settings changes.
3. Propose private `documents` bucket creation separately. No bucket existed at last verification. Confirm file size/MIME limits and prohibit public access; the backend service role mediates file reads. No direct client storage access is required.
4. Approve a separate empty test project and bounded provider usage before real integration tests. Never use private reports as test fixtures.

## Configuration

Backend: copy backend/.env.example. Supply SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY, HF_TOKEN, GROQ_API_KEY and ALLOWED_ORIGINS. Use a reviewed model identifier actually available to the provider account. Optional fallback requires LLM_FALLBACK_ENABLED=true plus OPENROUTER_API_KEY. Output has a configured cap. No client-chosen arbitrary model.

Frontend: copy frontend/.env.example. Set NEXT_PUBLIC_API_URL to the backend /api/v1 URL, NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY. Never expose service role/provider keys in NEXT_PUBLIC settings or client code. No project is hardcoded.

## Ingestion

- Inline (default): request parses, embeds and stores the report; intended for local use and small-file tests, not guaranteed within serverless time limits.
- Queue: use INGESTION_MODE=queue on a long-running host. Upload first stores a nonclaimable row and PDF, then changes state to queued. A failed storage write cannot create a claimable job. API worker claims, heartbeats and uses fenced database writes.
- Claims increment attempts; expired leases can retry up to three attempts. Old workers cannot write after loss of their fencing token. A lost worker can still waste billed embedding compute until its next fenced write.
- Render hosts the backend/worker. Vercel deploys only frontend; NEXT_PUBLIC_API_URL must point to the Render /api/v1 URL.
- Nonempty crash/restart recovery has local automated evidence, not a live Supabase end-to-end result.

## Release checklist

Run backend tests, local migration tests, frontend regression tests/typecheck/build. Review dependency advisories and scan repository/history/configuration for secrets. Review new migration 0004 and get target-specific approval before applying it; it changes delete/RLS behavior. Then on the isolated target test real login, signed uploads, PDF access, two-user isolation, deletion, queue recovery, provider failures and timeout handling. Record model/version, latency, quality, quota/cost and failed cases.

Do not release until private storage, distributed quotas, reviewed/apply-authorized migration 0004 and real Storage deletion tests, observability, secret rotation procedures and a backup/restore drill are addressed. The current in-memory rate limiter is per-process, not a shared quota. Table extraction is heuristic, not a verified accounting model. Citation ID validation does not prove semantic support.

Main merge is approved under the code-first sequence; manual deployment and paid resources still need separate approval. render.yaml is a proposal only. Root and /api/v1 routes are retained until deployed rewrites/clients are verified.
