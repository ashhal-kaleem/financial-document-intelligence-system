# Production readiness

Last verified 22 November 2026, late afternoon (IST). This is an evidence register, not a launch certificate. Current architecture: public no-login app with per-tab private guest sessions (Supabase anonymous sign-in), local ONNX MiniLM retrieval on Vercel, and server-side answers on the Groq free plan (`openai/gpt-oss-120b`). The Puter browser answer path and all login UI (Google + Puter) are removed.

Deployment provenance at verification time: `main` @ `0e9fc99`; frontend production READY on `0e9fc99` (auto-deploy from GitHub); backend production READY on `0e9fc99` (Vercel CLI deploy — the backend project has no git link). CI distinction: every push rebuilds the frontend; backend changes require a manual CLI redeploy, so a green frontend deploy never implies a current backend.

## Live-tested 22 November 2026 (production, real services)

- Fresh guest arrival creates an anonymous identity automatically; no login, modal or consent wall appears. Verified in a real browser session with screenshots.
- UI upload of a 1-page public financial PDF: processed inline to `ready` (1 page, embeddings computed server-side).
- Real answer through the UI's chat composer: "What was the revenue in fiscal year 2024?" returned "The document states that revenue for fiscal year 2024 was **USD 100 million**[1]." with a citation chip to the uploaded PDF, page 1. The citation chip opens an inspector with the exact passage extract, and its in-browser PDF viewer opens the PDF at the cited page. Model: `openai/gpt-oss-120b`.
- Cross-guest isolation: a second anonymous guest sees an empty library and gets 404 on the first guest's document and chunk endpoints (API-verified).
- Tab-scoped visibility: a second browser tab opened to the app shows an empty library; the first tab's PDF is not visible there (browser-verified).
- Dead-guest recovery: a tab whose anonymous identity was deleted server-side gets a 401, drops the dead session, signs in a fresh guest and retries automatically (browser-verified).
- "End session & delete my data" from the UI: deleted the guest's PDF (row, chunks, storage) and the anonymous identity, and a fresh guest session started. The backend also invalidates its token-verification cache for the ended identity, so its old tokens fail immediately; there is no residual acceptance window.
- Session deletion is guest-only: `DELETE /api/v1/session` rejects a non-anonymous caller with HTTP 403 before any document, usage or identity mutation. Verified live with a throwaway named test identity created for the probe (403 returned, identity confirmed unmodified afterwards, then removed).
- Cron: `GET /api/v1/internal/sweep` returns 401 without and with a wrong secret. Vercel lists the registered cron job `/api/v1/internal/sweep` on schedule `0 3 * * *`. The first actual scheduled fire has not happened yet.
- Orphaned guest cleanup: migration 0007's `sweep_orphaned_guest_users` RPC exists and is granted to the service role only (anonymous, zero documents, older than 25 hours).
- Concurrent guest-session starts within one tab share one in-flight sign-in. Same-moment duplicate anonymous identities were still observed in production after the dedupe deployed, consistent with stale cached bundles; this is a watch item, not declared fixed-in-production.

## Incidents during verification (fixed same day)

- The first live answer request returned HTTP 422 `invalid_citations`: `gpt-oss-120b` emits fullwidth citation markers (`【1】`) that the strict citation validator rejected. That request consumed two provider calls (initial + one regeneration) and one guest quota unit; no answer was shown. The backend now normalizes fullwidth markers to `[n]` before validation, with a regression test, and the live re-test above passed.
- Session deletion previously applied to any authenticated caller, including non-anonymous accounts. A resumed named session could therefore delete its own account and documents through the guest UI's "End session" action. Fixed: the endpoint is guest-only (see above). Total live Groq calls spent on verification: 6.

## Abuse and quota posture (honest bounds)

- Per-guest: 20 questions/day, 5 PDFs max, per-minute rate limits on API calls.
- Global: 60 answers/day (token-aware budget under the Groq free plan's 1K requests/day, 8K tokens/min, 200K tokens/day). Groq itself rejects beyond its free limits; there is no paid fallback anywhere in the code.
- Global upload admission: 100 documents / 200 MB per UTC day across all guests, enforced race-safe by migration 0008's `take_upload_quota` RPC before any storage or ingestion work, protecting shared free-tier storage and ingestion CPU. Verified live (counting and both exhaustion branches).
- Anonymous sign-in remains scriptable: per-guest limits multiply with fresh guests, and the global caps above are the real bound. A CAPTCHA on anonymous sign-in (Supabase supports Turnstile/hCaptcha) remains an available mitigation, not yet implemented.
- Groq account status: verified on the free plan at verification time. Plan terms can change; the app has no mechanism to become paid on its own.

## Data retention

- Guest uploads stop being accessible 24 hours after upload (`session_expires_at`); expired rows are force-deleted (row, chunks, stored PDF) by a traffic-ridden sweep plus the daily cron. Physical deletion happens at the next sweep, not at the exact 24-hour mark and not on browser close.
- Named (non-anonymous) accounts have no expiry, are never swept, and cannot be deleted through the guest session endpoint.
- Chat history and the guest identity live in the tab's sessionStorage only. Closing the tab abandons them; a new tab always starts empty. Browser "reopen closed tab", tab duplication or full session restore can resurrect a closed tab's storage; that is a current limitation of the app, not a guarantee.

## Local regression

Backend 155 passed, 2 skipped; frontend 29 passed; TypeScript and frontend production build passed. Counts are dated evidence, not a standing promise for future commits.

## Retrieval evaluation, limited evidence

A local re-encoding of 18 live public chunks, 30 authored expected-number checks and top-5 retrieval found 29/30 numbers (English 26/26, Hinglish 3/4). Known miss: `2025 ka poore saal ka net profit kitna hai?` did not retrieve the expected annual net income chunk within top 5. The runner and case file are under `backend/scripts/` and `backend/tests/evaluation/`.

## Remaining before stronger claims

1. First real Vercel cron fire (scheduled 03:00 UTC daily) has not been observed; the endpoint, auth and RPC are verified, the schedule registration is verified, the fire itself is not.
2. Broader labeled financial-report evaluation, correct period/column interpretation, abstention and Hinglish coverage. Citation validation checks marker identifiers, not semantic truth; answers must be checked against the cited page.
3. Concurrency/load tests, alerts, backup/restore drills. Successful requests and a free build are not production-capacity evidence.
4. OCR/scanned reports, reports over 4 MiB, cloud conversation history/export and analytics remain unimplemented. No commercial-use/uptime claim is made for Hobby/free tiers.

## Data and deployment discipline

Keep code/main, backend deployment and frontend deployment provenance separate: the frontend auto-deploys from GitHub; the backend has no git link and is deployed with the Vercel CLI from `backend/`. The suspended Render service/config remains a rollback artifact, not the current host.
