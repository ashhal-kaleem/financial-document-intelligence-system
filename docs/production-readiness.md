# Production readiness

Last verified 22 November 2026. This is an evidence register, not a launch certificate. Current backend runtime is local ONNX MiniLM on Vercel; the frontend's separate Puter answer path is unchanged.

## Completed

- Removed hosted HF embedding requests, HF token/configuration and direct HF inference dependency. Public HF model weights remain a build-time source only.
- Pinned all-MiniLM-L6-v2 revision, quantized ONNX bytes/tokenizer hashes, 384-dimensional profile, masked mean pooling and L2 normalization. Token-aware document splits and query rejection replace silent truncation.
- Cached single-thread CPU session, independent per-input execution, bounded work/lock wait, corrupted/missing asset checks and vector-profile mismatch refusal.
- Preserved private signed upload, owner filtering, browser PDF/citation viewer, safe-delete path and Puter as opt-in writer. No original app records were deleted/re-indexed or schema migrations applied by this rollout.
- Preserved and updated the five requested idea/context/test/launch notes. Active technical documentation now separates current implementation from old history.

## Live-tested

- Vercel Hobby preview and production backend builds succeeded with bundled public model. Runtime health checks database plus pinned assets; health explicitly does not claim inference was probed.
- A first-page extraction of Apple's official FY2025 Q4 financial statements, 3,554,148 bytes, passed the real signed-upload and inline-ingest path: one page, 18 chunks, ready. One ingestion took 3.205 seconds, not a latency distribution or load test. The full original PDF exceeded the current 4 MiB app cap, so this is not a whole-report success claim.
- Five actual production retrieval questions found the expected quarterly/annual numbers in context, with the selected document and page 1 citations.
- Cross-user document/chunk/PDF reads and delete returned 404; cross-user selected-document search returned zero chunks; unauthenticated library returned 401.
- Actual signed-in library, Q&A and PDF viewer were visually inspected. The ready PDF and separate AI-consent boundary displayed correctly. These temporary-user probes did not re-test the Google OAuth popup.
- Live document/chunk read policies are already strict owner-only, non-sample and hide deleting records. No new migration was needed or applied. A query below the schema character cap also returned the specific `embedding_input_too_long` 422 rather than truncating.

Local regression: backend 160 passed, 2 skipped; frontend 25 passed; TypeScript and frontend production build passed. Counts are dated evidence, not a standing promise for future commits.

## Retrieval evaluation, limited evidence

A local re-encoding of the 18 live public chunks, 30 authored expected-number checks and top-5 retrieval found 29/30 numbers. English 26/26, Hinglish 3/4. This set is one page and is not independently labeled, held out, multi-report or answer accuracy. It can overestimate support because number presence does not prove that a model chose the right row, year or column.

Known miss: `2025 ka poore saal ka net profit kitna hai?` did not retrieve the chunk containing the expected annual net income 112,010 within top 5. It remains a real limitation; no unsupported multilingual claim or hidden model substitution was made. The reproducible local-only runner and case file are under `backend/scripts/` and `backend/tests/evaluation/`.

## Remaining before end-to-end financial claims

1. **Actual Puter generation is unverified in this rollout.** Production Q&A requires a free-model selection, explicit report-disclosure consent and separate Puter account authorization. This check stopped at that boundary, without creating an account, authorizing a user's account or spending credits. At verification time all three configured model IDs were present with zero catalog rates. Catalog pricing is not a guarantee of remaining account allowance or service availability.
2. In the user's own session, connect Puter after reviewing the disclosure. A real generated answer must then be checked against source amount, unit, period, calculation and cited page. Stop on quota/pricing uncertainty. No paid fallback/topup or account-plan change is authorized.
3. Broader labeled financial-report evaluation, correct period/column interpretation, abstention and Hinglish coverage. Table context reduces lost headers but is not structured financial extraction or a semantic correctness proof. Citation validation checks identifiers/source access, not truth.
4. Concurrency/load tests, distributed admission/quota controls, alerts, backup/restore drills and an operational owner. The current budget/lock is per process. Successful requests and a free build are not production-capacity evidence.
5. OCR/scanned reports, larger reports, cloud conversation history/export and analytics remain unimplemented. No commercial-use/uptime claim is made for Hobby/free tiers.

## Data and deployment discipline

Keep code/main, backend deployment and frontend deployment provenance separate. A docs-only commit does not alter the running embedding behavior. Google/Supabase auth is distinct from Puter auth. The suspended Render service/config remains a rollback artifact, not the current host. Existing incompatible embeddings require a separately approved re-indexing plan; do not silently clear records.

Any future live probe must identify the owner, costs, source PDF, expected outputs and cleanup before making changes. The temporary public test PDF was deleted through the owner UI and both temporary users removed. Live cleanup verification returned the baseline: one pre-existing failed document metadata row preserved, zero chunks/vectors and zero private PDF objects. No original user record was removed.
