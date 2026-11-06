# Readiness evidence and release gates

Updated 6 November 2026. Source development is on backend-hardening; main may be fast-forwarded only after checked approval. This is not a production certification.

## Offline evidence

- Backend tests cover auth/scoping, queue fencing/heartbeat, storage and provider failures, size/type limits, citation marker rules, no-context answers and safety prompt requirements.
- Frontend regression tests cover owner-keyed browser history, legacy-key removal, fragmented UTF-8 SSE, incomplete/error/malformed streams, callback failure and deletion failure propagation.
- A 32-case synthetic financial seed covers currency/scale/year, basis, negative signs, precision, restatement, periods, missing data, hostile text/filenames, Hinglish and no context. Tests generate digital PDFs and check extraction/page/citation/prompt plumbing. They DO NOT run an LLM or measure answer quality.
- scripts/test_migrations.py uses throwaway local Postgres plus Supabase role/auth stubs. It tests RLS, search filters, queue retries/fencing and two-phase deletion. It is not a live Supabase/storage test.
- Frontend production build and typecheck are separate checks; they do not verify real authentication or hosted availability.

Latest local run:130 backend tests passed,2 live tests skipped;18 frontend regression tests passed;37 throwaway-Postgres checks passed;TypeScript,production build passed. Two backend dependency deprecation warnings remain. Mobile390px and desktop1280px screenshots inspected for Statements, auth prompt and honest export state. These are local results only.

Reproduce with README.md commands. Do not turn passing fixture tests into an accuracy percentage on a resume.

## New migration gate

0004_safe_document_delete.sql is NOT applied to a hosted project. It adds a service-role-only function that locks/owns a document, rejects deletion while upload/processing is active, marks it deleting and hides it from RLS reads. API deletion then removes the PDF via Storage API before deleting the database row and cascade chunks. Storage failure leaves a retry handle. Worker fenced writes reject deleting rows. Existing samples and other users' documents cannot be selected by the function.

Apply only after target schema/data/policies are inspected and the exact hosted change is approved. Deploying the new delete path without 0004 fails closed. No hosted migration is authorized merely by this file. Current approved hosted baseline was 0001-0003; new code needs 0004 for deletion.

A power loss between uploaded-row creation and queued state can leave a nonclaimable uploaded row. Reconciliation/admin cleanup with Storage is still needed. Long-running processing cannot be cancelled via delete; wait for completion or lease recovery. Account-deletion cascades still need storage-cleanup policy. These are release gaps, not completed outcomes.

## Decisions and live work remaining

- Working login provider and hosted redirect/client setup.
- Private bucket creation/configuration, then authenticated upload/PDF/delete and two-user isolation on a separate empty test target.
- User accepted Puter Connect with its genuine popup. Opt-in UI and receipt/marker checks are implemented but fake-tested only; no real generation or private data transfer has been run. Only exact free variants are allowlisted; no paid/provider fallback. This does not make usage unlimited, lock third-party prices atomically or remove HF embedding limits.
- Independently reviewed 30-50 question benchmark: retrieve expected evidence, run selected model under bounded approved usage, label numeric correctness, supported claims, citation support, abstention and injection behavior. Measure p50/p95, failure/retry rate and per-question cost on the same run. No live score exists yet.
- Shared per-user/daily cost quotas and concurrency controls. In-memory limiter remains per-process; output token cap is not a total budget.
- Metrics/alerts, dependency/security audit, secrets rotation and backup/restore exercise.
- Release approval; hosting budget/regions/privacy policies. Free Render proposal sleeps/has limited RAM and is not an always-on production promise.

## Privacy and correctness limits

ID validation checks only marker membership, not sentence-level grounding. Partial tokens are visible while streaming and replaced by an error if completion/validation fails. PDF table extraction can lose headings/structure. Local browser storage is not encrypted, and does not sync between devices. The old export implementation downloaded canned “verified/audit-ready” assertions rather than real analysis. It is removed; export now clearly says not implemented. Frontend sample financial screens remain illustrative and are always labeled, even with uploaded documents; static metrics are not relabeled as extracted from private reports.

## Current external references

- Storage deletion must use Storage API, not SQL metadata deletion: https://supabase.com/docs/guides/storage/management/delete-objects
- Storage API surface: https://supabase.github.io/storage/
- SMTP limitations: https://supabase.com/docs/guides/auth/auth-smtp
- Render free limits: https://render.com/docs/free

Puter response schema was checked against https://docs.puter.com/Objects/chatresponse/ and https://docs.puter.com/AI/chat/ . Normalized non-streamed responses document finish_reason and numeric usage.cost. Only stop + zero cost is accepted; missing/unknown metadata fails with a visible explanation. This is documented compatibility, not live proof for each provider. No actual generation or private-report transfer was performed.

Google Cloud access check: console.cloud.google.com requires account sign-in; no saved Google login or connected 1Password was available. Existing Cloud project/client existence remains unknown. Select the intended Google account before sign-in; request secrets through a secure vault link, never chat.


## 6 November follow-up: production data only

The deployed Overview and Documents screens still used hardcoded filing/activity fallbacks, even when the real library was empty. Statements, Comparison and Insights also contained fixed financial figures. The database reset did not remove these source-rendered values. These blocks and unused frontend seeds are now removed, not merely labeled. Unsupported analytics show an explicit unavailable state. The notification count and unsupported voice-input control were removed.

Overview totals now derive only from the authenticated non-sample document query. Signed-out, loading, failed-request and genuinely empty-library states are separate. Account-switch clearing and account-scoped chat-history behavior remain regression-tested; upload-modal state is remounted per account. Ready documents link to scoped Q&A and authenticated PDF view. No real login/upload/answer/delete workflow or cross-user isolation is claimed by these mocked/local tests.

The application API now filters every document lookup/list/retrieval scope to owner_id AND is_sample=false. Existing database sample/RLS policies are not changed by this source fix and still need a reviewed hosted policy decision. No database reset, private data deletion, storage or Google provider mutation is part of this cleanup.

Live Google sign-in currently navigates to Supabase HTTP400: provider is not enabled. This blocks the actual private workspace flow. Google setup, private storage, migration0004, zero-cost embeddings, real PDF/citation/deletion tests and operations checks remain release gates. Render Free sleep remains incompatible with a claimed always-on worker.

## Workspace route and recovery pass (6 November 2026)

- Real Next.js `/workspace`, `/documents`, `/qa` routes replace independent active-tab state; `/` and legacy `/chat` redirect. Shared desktop/mobile navigation and account entry, explicit Q&A Back link. Unsupported analysis pages retain honest unavailable states and are outside primary nav.
- Q&A requires one ready owned PDF selected in `?document=`. Unknown/inaccessible/not-ready scopes never silently expand to all documents. The server must still authorize IDs; URLs are not permission.
- Browser history is account AND document scoped. New conversation clears its saved record. Memory-only drafts survive route navigation, clear on account boundaries, and are not removed until a verified answer succeeds. Context errors preserve draft; cancel restores prior messages. No real provider call was made in these checks.
- Delete UI confirms, refuses busy processing rows, retains failure/retry and waits for server acknowledgement. Hosted migration 0004 is still required. Upload has PDF/25MB/empty validation and received-vs-ready status. Auth/upload use focus-trapped dialogs; Google disabled-provider preflight keeps the error inside the app.
- Citation inspector opens the PDF on explicit action; removed misleading “Verified Ground Truth” label. Successful citation-ID checks do not establish factual support.
- Local Playwright tests against a synthetic session/API/AI fixture verify direct/refresh/Back/Forward/same-active-tab, responsive guest/scope/unknown states, delete failure+retry, invalid upload, draft/error/cancel/history clear. These are local regression tests, not hosted Google, storage, AI, isolation or financial-quality proof. No fixture is included in production pages.
- Source migrations 0004/0005 now propose strict owned/non-sample direct reads. Applied twice only in disposable local Postgres with own-vs-other-vs-sample checks. No hosted schema/policy/bucket mutation is included in a code deployment.

## Duplicate controls cleanup (6 November, after 5:31 pm clarification)

Retained the chosen top rounded coloured Overview/Documents/Q&A tabs and all route/history behavior. Q&A now has one New conversation action in its header; the recent-question sidebar is shown only to signed-in users and has no duplicate reset button. Empty Documents/Overview use the empty-state upload action instead of repeating another upload action. Contextual guest Sign in and explicit Back to documents are intentional recovery actions, not a second tabs bar; preserved. No unsupported tabs/features restored and no auth/storage/schema changes.


## Repository maintenance (6 November, after audit)

Removed 18 reference-verified unreachable frontend modules, unused mock seed, their 20 public asset files (7,160,790 bytes), eight unused application dependencies, dead sidebar/export state and ignored styling props. App favicon stays. Test fixtures stay; backend Docker excludes them. Removed the unreachable sample PDF fallback. Production no longer rewrites to the deleted /api/index.py backend; local /api/v1 proxy stays. Compatibility API aliases and explicit server inference stay.

Security dependency remediation: Next 15.5.28, transitive sharp 0.35.5, PostCSS 8.5.32 and source-map-js 1.2.2 via reviewed overrides; certifi 2026.10.23 and filelock 4.2.9 in the Python lock. No model request/provider/schema change. Known-advisory scans are point-in-time, not a security certificate. pnpm 9 is used to resolve/check the lockfile; preserve it rather than rewriting with an incompatible package-manager generation.

Personal developer sync scripts remain because external use is unresolved; do not run or delete them automatically. Long-form historical planning files remain historical, not release truth. Further CSS cleanup, distributed quotas, backup/restore, observability, real financial accuracy and authenticated end-to-end evidence remain open.
