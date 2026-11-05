# Security Policy — Financial Document Intelligence System (FDIS)

## Reporting Vulnerabilities
Please report any security concerns or credential exposure directly to security@fdis.local.
All reports will be acknowledged within 24 hours.

## Policy Invariants
- Zero private credentials or API keys permitted in client bundles.
- All database queries must enforce tenant and document boundaries.

## Current controls (backend-hardening)
- Every data endpoint requires a Supabase user token (`Authorization: Bearer ...`), checked against Supabase Auth.
- Documents carry `owner_id`; list, read, chunks, PDF, delete and search are all scoped to the signed-in user. Shared samples are read-only.
- Upload and ask endpoints are rate limited per user (in memory, per process).
- Errors never return tracebacks or raw exception text; details go to server logs.
- CORS is limited to `ALLOWED_ORIGINS`. The open `/notify` email route was removed.
- Keep the Supabase storage bucket private and never expose the service-role key to the browser.
- `frontend/api/src` is a copy of `backend/src` for Vercel: run `scripts/sync-vercel-api.sh` after backend changes (CI checks it).
