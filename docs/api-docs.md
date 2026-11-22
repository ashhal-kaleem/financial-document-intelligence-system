# API contract overview

Source: `backend/src/api/routes` and the intended deployment's `/openapi.json`. Revised 22 November 2026. Base path `/api/v1`; root aliases remain for compatibility, not a second backend.

All document and ask endpoints require the user's Supabase Bearer token. Documents are owner-scoped and non-sample. Service-role/provider keys never go to the browser. CORS uses configured frontend origins.

## Health and documents

- `GET /health`: cached database probe plus pinned local-model asset integrity. Embedding status `local_assets_verified` is an asset check, not a model inference or final-answer test. Returns 503 if required DB/assets checks fail. Optional provider configuration is explicitly unverified.
- `GET /documents`: own non-sample library and processing status.
- `POST /documents/upload-url`: validate filename/reported size, create owned non-ready row and issue one-object private upload capability. The browser uploads through Supabase, then calls ingest.
- `POST /documents/{id}/ingest`: recheck stored-object size, atomically claim and process inline. Error is not ready. App acceptance is currently 4 MiB; bucket admission is separate.
- `DELETE /documents/{id}` also handles cancellation of abandoned upload state through the fenced marker flow; it is not a separate cancel-upload route.
- `POST /documents`: compatibility multipart path; 201 inline-ready or 202 queue-accepted on a long-running host. Vercel forces inline.
- `GET /documents/{id}`: own document row.
- `GET /documents/{id}/chunks`: own evidence passages and page metadata.
- `GET /documents/{id}/pdf`: authorized private/no-store PDF bytes.
- `DELETE /documents/{id}`: owner-only deletion through the safe-delete RPC/storage path. Busy states return conflict. Storage failure retains a retry handle; it is not reported as successful cleanup.

The parser rejects empty, scanned-only and encrypted PDFs. Default page/chunk/work limits are in config. Document chunks are tokenizer-bounded rather than silently truncated. The 256-token query ceiling is additional to the request schema's 2-4000 characters/at-most 100 document IDs.

## Retrieval and opt-in answers

- `POST /ask/context`: authenticated local MiniLM retrieval inspection: grounded messages, citations and chunks_count. It does not call a language model or write an answer.
- `GET /ask/browser-models`: the application's exact provider-qualified free-model allowlist. It is not proof that every listed model is currently available.
- `POST /ask/browser-context`: requires consent plus an allowed model; retrieves owned passages and checks zero catalog pricing, then returns messages/citations and a signed owner/expiry receipt. A no-context answer is fixed and makes no model call.
- `POST /ask/browser-validate`: validates receipt, citation marker IDs and current source visibility. Returns `semantic_support_verified=false`; it does not prove model provenance, financial correctness or semantic support.

Actual Puter generation happens separately in the authorized user's browser. There is no `/ask/stream` server-inference endpoint after Groq removal. OpenRouter fallback remains configured-off and is not part of this rollout.

Returned vector matches with a different or missing embedding profile fail with 409 instead of mixing vector spaces. Too-long search text fails 422; busy/exceeded local inference budgets fail 503. The limiter/encoder lock is per process, not distributed.

Application errors use `success=false`, `error` and `meta`; framework HTTP errors can use `detail`. Never log tokens or rely on old example responses as current service evidence. Confirm route spelling against OpenAPI before integrating.
