# API contract overview

Source reference: backend/src/api/routes and /openapi.json from the intended deployment. Base development path: http://localhost:8000/api/v1. Root aliases are retained for deployed-client compatibility, not a second service.

All document and ask endpoints require Authorization: Bearer <Supabase access token>. Owner-scoped data includes explicitly shared read-only samples. Service-role/provider keys never go to the browser. CORS uses ALLOWED_ORIGINS.

- GET /health: current cached database probe, with 30-second TTL. Provider fields report configured_unverified or unconfigured, not a model call or all-service readiness guarantee. 503 on database failure.
- GET /documents: accessible document rows and processing status.
- POST /documents: PDF multipart upload, size/type/page safety checks. 201 inline-ready; 202 queue-accepted. Error state is not ready.
- GET /documents/{id}: one accessible row.
- GET /documents/{id}/chunks: accessible evidence passages.
- GET /documents/{id}/pdf: authorized private/no-store PDF response.
- DELETE /documents/{id}: owned, nonsample document; 409 while upload/processing is active. New path requires migration 0004. Storage failures do not report success; retry deleting state.
- POST /ask/context: authenticated retrieval-inspection result: messages, citations, chunks_count. Does not generate an answer.
- POST /ask/stream: SSE stage/citations/token/done or error. Client must see done plus terminal [DONE]; EOF/error/malformed data is failure. done reports stream_chunks, not provider token usage. Only configured model allowed.

Input limits: question 2-4000 characters, at most100 document IDs. See source config for upload/page limits. Upload/ask limiter is per-user/per-process, not distributed; no rate-limit headers are promised.

Errors use success=false, error {code,message,title,details} and meta {timestamp,path}. The content type may be application/problem+json, but the body is this app-specific envelope, not an exact RFC9457 object. Framework HTTP exceptions may use detail. Never rely on old specimen responses as live health evidence.
