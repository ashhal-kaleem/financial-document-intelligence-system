# Project Idea & Master Specification: Financial Document Intelligence System (FDIS)

> **Instructions for Fresh Session**: Copy and paste the prompt in Section 1 into your new chat to trigger the full systematic build lifecycle according to `/home/shaikhfardin/templates/instructions.md`.

---

## 📋 Section 1: The Master Kickoff Prompt (Copy-Paste This into New Session)

```markdown
I want to build an enterprise-grade **Financial Document Intelligence System (FDIS)** from scratch following `/home/shaikhfardin/templates/instructions.md`.

### 🎯 Core Vision
A high-accuracy, production-ready AI assistant designed for corporate financial analysts, auditors, and investors to upload complex corporate annual reports (PDFs) and perform sub-second, strictly grounded Q&A with verifiable page-level citations and real-time streaming.

### 🏛️ Required Architecture & Tech Stack:
1. **Frontend**:
   - Next.js 16 (App Router), React 19, Tailwind CSS v4 with OKLCH theme tokens.
   - shadcn/ui atomic components, Lucide icons, Framer Motion transitions.
   - TanStack Query v5 with `useHydrated` guard.
   - Real-time token-by-token SSE streaming response consumer.
   - 5 UI states on every screen (Ideal, Empty, Loading Skeleton, Error with retry, Partial).
   - Document upload drawer with progress bar, active document selector, and citation inspector panel.

2. **Backend Engine**:
   - Python FastAPI with 4-Tier Architecture (API Router -> Service -> Domain -> Infrastructure).
   - Fast native C-engine PDF parsing via PyMuPDF (`fitz`) and recursive financial chunking (512 char target, 64 overlap).
   - Dense vector embeddings via `all-MiniLM-L6-v2` (384 dimensions).
   - Serverless Vector Database: Supabase PostgreSQL with `pgvector` extension and custom `match_chunks` cosine similarity RPC function.
   - LLM Inference: Ultra-fast Groq LPU (`qwen/qwen3.8-27b`) with OpenRouter transparent fallback chain.
   - Real-time token streaming via Server-Sent Events (SSE) on `/ask/stream`.
   - Email notifications via Resend REST API.

3. **Sample Reports**:
   - Copy or ingest samples from `/home/shaikhfardin/Downloads/data/samples/ABL_Annual_Report_2025.pdf` and `HBL_Annual_Report_2025.pdf`.

Please execute strictly through `/home/shaikhfardin/templates/instructions.md` starting with Phase 0 (Research Approval Gate) and Phase 1 documentation.
```

---

## 🛠️ Section 2: Verified Cloud Credentials (`~/.backend_tokens.env`)
The following 100% Free & Zero-Card cloud engines are pre-verified and available on the system:
- **Supabase Project URL**: `https://aluzqooagiymysssnhkg.supabase.co`
- **Supabase DB & pgvector**: Postgres 17.6 in Mumbai (`ap-south-1`) with `vector(384)`
- **Supabase Storage Bucket**: `documents`
- **Groq AI Engine**: `qwen/qwen3.8-27b` (sub-second inference)
- **OpenRouter Free Router**: `nvidia/nemotron-3.5-lightning:free` / `liquid/lfm-2.5-2.6b:free`
- **Resend Email**: Verified transactional sending key
- **Upstash Redis & QStash**: Serverless cache and cron queue

---

## 📑 Section 3: Essential Functional Requirements
1. **PDF Ingestion & Chunking**:
   - Extract multi-page corporate balance sheets, P&L statements, and notes.
   - Preserve `filename`, `page_number`, and `chunk_index` in metadata.
2. **Grounded Retrieval & Anti-Hallucination**:
   - Cosine similarity matching via `match_chunks` RPC.
   - Zero-hallucination prompt: if facts are missing from the report, state clearly that the figure is not disclosed in the text.
   - Verifiable citation format: `[1] filename, p.X (chunk Y/Z)`.
3. **Interactive UI**:
   - Left Sidebar: Document list, upload button, upload progress, document statistics.
   - Main Chat Area: Message history, source citation badges with drawer preview.
   - Chat Input: Sticky prompt box with model selector and query suggestions.
