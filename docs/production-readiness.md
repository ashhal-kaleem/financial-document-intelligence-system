# Production readiness

Last verified 22 November 2026, evening (IST). This is an evidence register, not a launch certificate. Current architecture: public no-login app with per-tab private guest sessions (Supabase anonymous sign-in), local ONNX MiniLM retrieval on Vercel, and server-side answers on the Groq free plan (`openai/gpt-oss-120b`). The Puter browser answer path and all login UI (Google + Puter) are removed.

## Live-tested 22 November 2026 (production, real services)

- Fresh guest arrival creates an anonymous identity automatically; no login, modal or consent wall appears. Verified in a real browser session with screenshots.
- UI upload of a 1-page public financial PDF: processed inline to `ready` (1 page, embeddings computed server-side).
- Real answer through the UI's API path: "What was the revenue in fiscal year 2024?" returned "The document states that revenue for fiscal year 2024 was USD 100 million[1]." with a citation to the uploaded PDF, page 1. Model: `openai/gpt-oss-120b`.
- Cross-guest isolation: a second anonymous guest sees an empty library and gets 404 on the first guest's document and chunk endpoints (API-verified).
- Tab-scoped visibility: a second browser tab opened to the app shows an empty library; the first tab's PDF is not visible there (browser-verified).
- "End session & delete my data" from the UI: deleted the guest's PDF (row, chunks, storage) and the anonymous identity (`documents_deleted: 1, identity_removed: true`), and a fresh guest session started. The Documents screen showed empty afterwards (browser-verified).
- Deleted identity rejection: GoTrue returns 403 for a deleted user's token; the backend returns 401. During the backend's 60-second verification cache window right after deletion, the token can still authenticate, but all data is already gone and writes fail at the database (foreign key). This window is a known, bounded residual.
- Cron: `GET /api/v1/internal/sweep` returns 401 without and with a wrong secret. Vercel lists the registered cron job `/api/v1/internal/sweep` on schedule `0 3 * * *`. The first actual scheduled fire has not happened yet.
- Orphaned guest cleanup: migration 0007's `sweep_orphaned_guest_users` RPC exists and is granted to the service role only; test identities created during verification were deleted immediately and the daily cron sweeps the rest (anonymous, zero documents, older than 25 hours).
- Concurrent guest-session starts are deduplicated: a fresh tab creates exactly one anonymous identity.

## Incident during verification (fixed same day)

The first live answer request returned HTTP 422 `invalid_citations`: `gpt-oss-120b` emits fullwidth citation markers (`【1】`) that the strict citation validator rejected. That request consumed two provider calls (initial + one regeneration) and one guest quota unit; no answer was shown. The backend now normalizes fullwidth markers to `[n]` before validation, with a regression test, and the live re-test above passed. Total live Groq calls spent on verification: 5.

## Abuse and quota posture (honest bounds)

- Per-guest: 20 questions/day, 5 PDFs max, per-minute rate limits on API calls.
- Global: 60 answers/day (token-aware budget under the Groq free plan's 1K requests/day, 8K tokens/min, 200K tokens/day). Groq itself rejects beyond its free limits; there is no paid fallback anywhere in the code.
- Open risk: anonymous sign-in is scriptable, so per-guest limits do not stop an attacker from creating many guests. The global answer cap bounds answer spend, but uploads, storage (Supabase free tier), database rows and ingestion CPU are not globally capped. A CAPTCHA on anonymous sign-in (Supabase supports Turnstile/hCaptcha) and/or a global daily upload cap remain available mitigations, not yet implemented.
- Groq account status: verified on the free plan at verification time. Plan terms can change; the app has no mechanism to become paid on its own.

## Data retention

- Guest uploads carry a 24-hour `session_expires_at`; expired rows are force-deleted (row, chunks, stored PDF) by a traffic-ridden sweep plus the daily cron. Physical deletion happens at sweep time, not at the exact 24-hour mark and not on browser close.
- The one pre-existing document (the owner's old Google-account PDF) is untouched, never public, and inaccessible from the guest-only UI. Old named accounts have no expiry and are never swept. Deleting that old data would need a separate explicit decision.
- Chat history and the guest identity live in the tab's sessionStorage only. Browser "reopen closed tab" or full session restore can resurrect a closed tab's storage; that is browser behavior outside the app's control.

## Local regression

Backend 152 passed, 2 skipped; frontend 27 passed; TypeScript and frontend production build passed. Counts are dated evidence, not a standing promise for future commits.

## Retrieval evaluation, limited evidence

A local re-encoding of 18 live public chunks, 30 authored expected-number checks and top-5 retrieval found 29/30 numbers (English 26/26, Hinglish 3/4). Known miss: `2025 ka poore saal ka net profit kitna hai?` did not retrieve the expected annual net income chunk within top 5. The runner and case file are under `backend/scripts/` and `backend/tests/evaluation/`.

## Remaining before stronger claims

1. First real Vercel cron fire (scheduled 03:00 UTC daily) has not been observed; the endpoint, auth and RPC are verified, the schedule registration is verified, the fire itself is not.
2. Broader labeled financial-report evaluation, correct period/column interpretation, abstention and Hinglish coverage. Citation validation checks marker identifiers, not semantic truth; answers must be checked against the cited page.
3. Concurrency/load tests, distributed admission control beyond the current quotas, alerts, backup/restore drills. Successful requests and a free build are not production-capacity evidence.
4. OCR/scanned reports, reports over 4 MiB, cloud conversation history/export and analytics remain unimplemented. No commercial-use/uptime claim is made for Hobby/free tiers.

## Data and deployment discipline

Keep code/main, backend deployment and frontend deployment provenance separate: the frontend auto-deploys from GitHub; the backend has no git link and is deployed with the Vercel CLI from `backend/`. The suspended Render service/config remains a rollback artifact, not the current host.
