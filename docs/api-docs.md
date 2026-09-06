# API Documentation & Contracts — Financial Document Intelligence System (FDIS)

> **Status**: Approved  
> **Base URL (Development)**: `http://localhost:8000/api/v1`  
> **Master Protocol**: `/home/shaikhfardin/templates/instructions.md`  
> **Last Updated**: 2026-09-06

---

## 1. Global API Conventions

- **Content-Type**: `application/json; charset=utf-8` (or `text/event-stream` for SSE)
- **Error Standard**: RFC 9457 Problem+JSON format
- **Rate Limit Headers**: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`
- **CORS**: Configured for local Next.js frontend (`http://localhost:3000`) and production origins.

---

## 2. Standardized Error Envelope (RFC 9457 Problem+JSON)

All error responses return structured JSON:
```json
{
  "type": "https://api.fdis.local/errors/validation-failed",
  "title": "Validation Failed",
  "status": 422,
  "detail": "The uploaded file must be a valid PDF format.",
  "instance": "/api/v1/documents",
  "code": "validation_error"
}
```

---

## 3. Endpoints Specification

### 3.1 Health & Diagnostic

#### `GET /health`
Returns system component readiness and database connectivity.

**Response `200 OK` (`application/json`)**:
```json
{
  "status": "healthy",
  "database": "connected",
  "groq": "available",
  "openrouter": "available",
  "version": "1.0.0"
}
```

---

### 3.2 Document Management

#### `POST /documents` (Upload & Ingest PDF)
Accepts a PDF file, parses pages, extracts tables, computes dense embeddings, and persists chunks to Supabase `chunks`.

**Request Body (`multipart/form-data`)**:
- `file`: PDF binary (< 25MB)

**Response `201 Created` (`application/json`)**:
```json
{
  "id": "e4b2d35c-8df2-4217-b70d-f210d7a6e112",
  "filename": "apple_10k_2024.pdf",
  "page_count": 78,
  "chunk_count": 245,
  "status": "ready",
  "created_at": "2026-09-06T03:15:00Z"
}
```

#### `GET /documents` (List Documents)
Returns all ingested documents with status and chunk counts.

**Response `200 OK` (`application/json`)**:
```json
{
  "data": [
    {
      "id": "e4b2d35c-8df2-4217-b70d-f210d7a6e112",
      "filename": "apple_10k_2024.pdf",
      "page_count": 78,
      "chunk_count": 245,
      "status": "ready",
      "created_at": "2026-09-06T03:15:00Z"
    }
  ],
  "total": 1
}
```

#### `DELETE /documents/{id}` (Delete Document)
Deletes a document and cascades deletion across all related vector chunks.

**Response `200 OK`**:
```json
{
  "deleted": true,
  "id": "e4b2d35c-8df2-4217-b70d-f210d7a6e112"
}
```

---

### 3.3 Financial Intelligence & Grounded Q&A

#### `POST /ask/stream` (Real-Time SSE Inference)
Streams token-by-token answer with verifiable citations and stage events.

**Request Body (`application/json`)**:
```json
{
  "question": "What was the total net revenue and operating income for 2024?",
  "document_ids": ["e4b2d35c-8df2-4217-b70d-f210d7a6e112"],
  "model": "groq/qwen3.8-27b"
}
```

**Response `200 OK` (`text/event-stream`)**:
```text
data: {"event": "stage", "stage": "retrieving", "detail": "Executing cosine similarity search in pgvector"}

data: {"event": "citations", "citations": [{"citation_id": 1, "filename": "apple_10k_2024.pdf", "page": 32, "chunk_index": 45, "total_chunks": 245, "similarity": 0.842, "snippet": "Total net sales were $391,035 million..."}]}

data: {"event": "token", "token": "According"}

data: {"event": "token", "token": " to"}

data: {"event": "token", "token": " the"}

data: {"event": "token", "token": " Consolidated"}

data: {"event": "token", "token": " Statements"}

data: {"event": "token", "token": " of"}

data: {"event": "token", "token": " Operations [1]"}

data: {"event": "done", "finish_reason": "stop", "total_tokens": 128}

data: [DONE]
```

---

### 3.4 Notifications & Audit Alerts

#### `POST /notify` (Send Audit Email Report)
Sends an email summary of document analysis via Resend API.

**Request Body (`application/json`)**:
```json
{
  "recipient": "analyst@firm.com",
  "document_name": "apple_10k_2024.pdf",
  "summary": "Key metrics analyzed: Revenue $391.0B, Operating Margin 31.2%."
}
```

**Response `200 OK`**:
```json
{
  "success": true,
  "message_id": "3e06b38b-3c0e-4057-b939-8c5816c142f8"
}
```
