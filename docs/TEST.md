# Testing Strategy & Quality Review Gates — Financial Document Intelligence System (FDIS)

> **Status**: Approved  
> **Master Protocol**: `/home/shaikhfardin/templates/instructions.md`  
> **Last Updated**: 2026-09-06

---

## 1. Quick Smoke-Test Suite (Terminal)

```bash
# 1. Environment and Runtimes
python3 --version
node -v

# 2. Backend Unit & Contract Tests
cd backend && uv run pytest -v

# 3. Frontend Typecheck
cd frontend && pnpm run typecheck
```

---

## 2. Live Dependency Reachability Verification

| Dependency | Verification Command | Expected Status |
|---|---|---|
| **Supabase REST & Storage** | `curl -s "${SUPABASE_URL}/storage/v1/bucket" -H "apikey: ${SUPABASE_SERVICE_ROLE_KEY}"` | `200 OK` (includes `documents` bucket) |
| **Supabase pgvector** | SQL query `pg_extension WHERE extname = 'vector'` | `vector 0.8.2` |
| **Groq LPU Engine** | `curl -s https://api.groq.com/openai/v1/models -H "Authorization: Bearer $GROQ_API_KEY"` | `200 OK` |
| **OpenRouter Router** | `curl -s https://openrouter.ai/api/v1/chat/completions ...` | `200 OK` |
| **Resend Email API** | `curl -s https://api.resend.com/emails ...` | `200 OK` |

---

## 3. Deep Diagnostic & End-to-End API Smoke Tests

### 3.1 Health Diagnostic (`GET /api/v1/health`)
```bash
curl -s http://localhost:8000/api/v1/health | jq .
```

### 3.2 Document Upload & Indexing (`POST /api/v1/documents`)
```bash
curl -s -X POST http://localhost:8000/api/v1/documents \
  -F "file=@sample_report.pdf" | jq .
```

### 3.3 Real-Time SSE Inference (`POST /api/v1/ask/stream`)
```bash
curl -N -s -X POST http://localhost:8000/api/v1/ask/stream \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the net profit?", "document_ids": []}'
```
