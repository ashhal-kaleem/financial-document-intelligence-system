# Readiness evidence and release gates

Updated 6 November 2026. Source changes are on backend-hardening only. This is not a production certification.

## Offline evidence

- Backend tests cover auth/scoping, queue fencing/heartbeat, storage and provider failures, size/type limits, citation marker rules, no-context answers and safety prompt requirements.
- Frontend regression tests cover owner-keyed browser history, legacy-key removal, fragmented UTF-8 SSE, incomplete/error/malformed streams, callback failure and deletion failure propagation.
- A 32-case synthetic financial seed covers currency/scale/year, basis, negative signs, precision, restatement, periods, missing data, hostile text/filenames, Hinglish and no context. Tests generate digital PDFs and check extraction/page/citation/prompt plumbing. They DO NOT run an LLM or measure answer quality.
- scripts/test_migrations.py uses throwaway local Postgres plus Supabase role/auth stubs. It tests RLS, search filters, queue retries/fencing and two-phase deletion. It is not a live Supabase/storage test.
- Frontend production build and typecheck are separate checks; they do not verify real authentication or hosted availability.

Latest local run:130 backend tests passed,2 live tests skipped;18 frontend regression tests passed;37 throwaway-Postgres checks passed;TypeScript,production build and mirror check passed. Two backend dependency deprecation warnings remain. Mobile390px and desktop1280px screenshots inspected for Statements, auth prompt and honest export state. These are local results only.

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
- Main merge and release approval; hosting budget/regions/privacy policies. Free Render proposal sleeps/has limited RAM and is not an always-on production promise.

## Privacy and correctness limits

ID validation checks only marker membership, not sentence-level grounding. Partial tokens are visible while streaming and replaced by an error if completion/validation fails. PDF table extraction can lose headings/structure. Local browser storage is not encrypted, and does not sync between devices. The old export implementation downloaded canned “verified/audit-ready” assertions rather than real analysis. It is removed; export now clearly says not implemented. Frontend sample financial screens remain illustrative and are always labeled, even with uploaded documents; static metrics are not relabeled as extracted from private reports.

## Current external references

- Storage deletion must use Storage API, not SQL metadata deletion: https://supabase.com/docs/guides/storage/management/delete-objects
- Storage API surface: https://supabase.github.io/storage/
- SMTP limitations: https://supabase.com/docs/guides/auth/auth-smtp
- Render free limits: https://render.com/docs/free

Puter response schema was checked against https://docs.puter.com/Objects/chatresponse/ and https://docs.puter.com/AI/chat/ . Normalized non-streamed responses document finish_reason and numeric usage.cost. Only stop + zero cost is accepted; missing/unknown metadata fails with a visible explanation. This is documented compatibility, not live proof for each provider. No actual generation or private-report transfer was performed.

Google Cloud access check: console.cloud.google.com requires account sign-in; no saved Google login or connected 1Password was available. Existing Cloud project/client existence remains unknown. Select the intended Google account before sign-in; request secrets through a secure vault link, never chat.
