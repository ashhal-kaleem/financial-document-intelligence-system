# Financial Document Intelligence System (FDIS)

[![Codespaces](https://img.shields.io/badge/Codespaces-Open_in_Cloud-blue?logo=github)](https://codespaces.new/ashhal-kaleem/financial-document-intelligence-system?quickstart=1)
[![Backend](https://img.shields.io/badge/FastAPI-0.141-009688?logo=fastapi)](backend/)
[![Frontend](https://img.shields.io/badge/Next.js-16_React_19-black?logo=next.js)](frontend/)
[![Database](https://img.shields.io/badge/Supabase-pgvector_0.8.2-3ECF8E?logo=supabase)](https://supabase.com)
[![Quality Gate](https://img.shields.io/badge/Playbook_Audit-100%25_PASS-success)](systematic-build.md)

> **Enterprise-grade Corporate PDF RAG Pipeline for Sub-Second Balance Sheet, Footnote & Debt Covenant Q&A with Verifiable Citations and Zero Hallucination.**

---

## ⚡ 1-Click Cloud Launch (Zero-Laptop Load)

Don't want to heat up your local laptop or install local dependencies? Launch the full stack directly in **GitHub Codespaces**:

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/ashhal-kaleem/financial-document-intelligence-system?quickstart=1)

- **Machine**: Up to 32-core cloud Linux VMs.
- **Pre-configured**: Python 3.12, Node.js LTS, `uv`, and `pnpm`.
- **Automatic Ports**: Ports `3000` (Next.js) and `8000` (FastAPI) automatically forwarded.
- **Laptop Benefit**: Local CPU and RAM usage remains near 0%.

---

## 🏛️ System Architecture (Pragmatic 4-Tier Clean Architecture)

```
[User / Browser]
       │
       ▼
[Next.js 16 + React 19 Frontend]
       │ (TanStack Query v5 / Server-Sent Events)
       ▼
[FastAPI 4-Tier Backend]
  ├── src/api/               (REST & SSE Endpoints under /api/v1)
  ├── src/services/          (Ingestion, Retrieval, Inference, Notification)
  ├── src/domain/            (Recursive Financial Chunker & Citations)
  └── src/infrastructure/    (Supabase pgvector, Groq LPU, OpenRouter, Resend)
       │
       ▼
[Cloud Persistence & Inference]
  ├── Supabase PostgreSQL 17.6 + pgvector 0.8.2 (Cosine Distance RPC)
  ├── Groq LPU (Qwen 2.5 32B / 70B sub-second streaming)
  └── OpenRouter Multi-Model Fallback Array (LFM-2.5, Nemotron, MiniMax)
```

---

## ✨ Key Features

1. **Table-Aware Recursive Financial Chunker**:
   - 512-character target with 64-character overlap.
   - Detects financial table markers (`|`, `---`, tabular numerals) to prevent breaking balance sheets across chunk boundaries.
2. **Zero-Hallucination Non-Disclosure**:
   - Strict system prompt refusal: if financial facts are absent or below cosine similarity threshold, the model explicitly refuses to speculate.
3. **Interactive Citation Inspector Drawer**:
   - Verified inline badges (e.g. `[1] p.204`).
   - Slide-out inspector displays source filing, page number, cosine similarity score, and verbatim excerpt.
4. **Resilient LLM Routing & SSE Defense**:
   - Transparent fallback from Groq LPU to OpenRouter models.
   - Client disconnect guard (`if await request.is_disconnected(): break`) halts upstream token billing immediately.
5. **Full Playbook Invariant Compliance**:
   - Unified API response envelopes (`{"success": true, "data": ..., "meta": ...}`).
   - RFC 9457 compliant error responses.
   - TanStack Query server state + Zustand client state boundary.
   - Accessible shadcn/ui primitives with `tabular-nums` formatting.

---

## 🚀 Local Quickstart

### Prerequisites
- Python 3.12+ and [uv](https://astral.sh/uv)
- Node.js 20+ and [pnpm](https://pnpm.io)

### 1. Run Backend
```bash
cd backend
uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation: `http://localhost:8000/docs`  
Live Diagnostic Healthcheck: `http://localhost:8000/api/v1/health`

### 2. Run Frontend
```bash
cd frontend
pnpm install
pnpm dev
```
Open `http://localhost:3000` in your browser.

---

## 🧪 Verification & Testing

Execute full automated validation:

```bash
# 1. Playbook Compliance Audit (Law of Quality)
python3 /home/shaikhfardin/templates/scripts/verify-playbook.py .

# 2. Run Backend Unit & E2E Test Suite
cd backend && uv run pytest -v

# 3. Typecheck Frontend
cd frontend && pnpm run typecheck
```

---

## 📚 Project Documentation

- [Product Requirements Document (PRD)](docs/PRD.md)
- [System Architecture Specification](docs/architecture.md)
- [API Contracts & RFC 9457 Schemas](docs/api-docs.md)
- [Production Deployment Runbook](docs/deployment.md)
- [Test Strategy & Healthcheck Runbook](docs/TEST.md)
- [GTM & Launch Kit](docs/GTM_LAUNCH_KIT.md)
- [Master Agent Handbook (AGENTS.md)](AGENTS.md)

---

## 📄 License
MIT License. Built with the Sovereign Developer Protocol.
