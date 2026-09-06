# Systematic Build Checklist — Financial Document Intelligence System (FDIS)

> **Phased Build Engine & Atomic Verification Checklist**  
> Companion file to `instructions.md` and `AGENTS.md`.

---

## 📋 Phased Build Progress

### Phase 1 — Foundations & External Dependency Verification
- [x] **Supabase pgvector (Postgres 17.6)** → verified
- [x] **Supabase Storage (documents bucket)** → verified
- [x] **Groq LPU Engine (qwen3.8-27b)** → verified
- [x] **OpenRouter Router (liquid/lfm-2.5-2.6b:free)** → verified
- [x] **Resend Email API** → verified

---

### Phase 2 — Backend Engine Architecture & Scaffolding
- [x] **Step 2.1**: Backend dependencies setup via `uv` → verified: `import fitz, sentence_transformers, fastapi`
- [x] **Step 2.2**: Config & environment validation (`src/core/config.py`) → verified: `Config valid: https://aluzqooagiymysssnhkg.supabase.co`
- [x] **Step 2.3**: Domain Layer (`models.py`, `chunker.py`, `citation.py`) → verified: `pytest tests/test_chunker.py -v` (3 passed)
- [x] **Step 2.4**: Infrastructure Layer (`supabase_client.py`, `groq_client.py`, `openrouter_client.py`, `embedding_client.py`, `resend_client.py`) → verified: `pytest tests/test_infrastructure.py -v` (4 passed)
- [x] **Step 2.5**: Service Layer (`ingestion.py`, `retrieval.py`, `inference.py`, `notification.py`) → verified: `pytest tests/test_services.py -v` (2 passed)
- [x] **Step 2.6**: API Routers (`health.py`, `documents.py`, `ask.py`, `notify.py`) → verified: `pytest tests/test_api.py -v` (3 passed)

---

### Phase 3 — Real-Time Streaming & End-to-End Verification
- [x] **Step 3.1**: PDF Ingestion roundtrip with real financial PDF → verified: `sample_apple_10k.pdf` ingested to Supabase
- [x] **Step 3.2**: SSE Stream `/api/v1/ask/stream` with real token streaming & citations → verified: `test_e2e_ingestion_and_streaming.py` PASSED

---

### Phase 4 — Frontend UI/UX (Next.js 16 + React 19 + Tailwind v4 OKLCH)
- [x] **Step 4.1**: Bootstrap `frontend/` with Next.js 16, React 19, Tailwind v4 OKLCH → verified: `next build` PASSED
- [x] **Step 4.2**: Configure TanStack Query v5 with `useHydrated` guard → verified: `pnpm run typecheck` (0 errors)
- [x] **Step 4.3**: Left Sidebar (document upload, progress bar, active filing filter) → verified in live browser
- [x] **Step 4.4**: Main Chat Interface with 5 UI states and real-time SSE stream consumer → verified in live browser
- [x] **Step 4.5**: Citation Inspector Drawer (previewing source page, chunk index, similarity gauge, and snippet) → verified in live browser

---

### Phase 5 — Multi-Lens Review & Quality Gate
- [x] **Step 5.1**: Secret leak audit: `grep -rn "API_KEY\|SERVICE_ROLE\|SECRET" frontend/src/` → verified: 0 secrets exposed (PASSED)
- [x] **Step 5.2**: Unhappy path & chaos tests (empty files, non-PDF rejection, 429 quota shifting, zero-hallucination non-disclosure) → verified: all chaos tests passed (PASSED)
- [x] **Step 5.3**: Playbook & Template Invariant Compliance Gate (`python3 /home/shaikhfardin/templates/scripts/verify-playbook.py .`) → verified: 0 violations, 0 warnings (PASSED)
