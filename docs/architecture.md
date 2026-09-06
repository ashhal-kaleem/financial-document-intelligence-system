# Architecture & System Blueprint — Financial Document Intelligence System (FDIS)

> **Status**: Approved  
> **Approved Architecture Approach**: Approach 3 (Pragmatic Enterprise 4-Tier Clean Architecture)  
> **Master Protocol**: `/home/shaikhfardin/templates/instructions.md`  
> **Last Updated**: 2026-09-06

---

## 1. High-Level Architecture & System Topology

### 1.1 Overview
FDIS follows a strictly decoupled **4-Tier Clean Architecture**:
1. **Presentation Layer (Frontend)**: Next.js 16 (App Router), React 19, Tailwind CSS v4 `@theme inline` with OKLCH tokens, TanStack Query v5 with `useHydrated` guard, Framer Motion, and SSE stream consumer with 5 UI states.
2. **API Router Layer (FastAPI)**: HTTP REST routes (`/api/v1/documents`, `/api/v1/ask/stream`, `/api/v1/health`, `/api/v1/notify`) performing schema validation and request dispatching.
3. **Application Service Layer**: Orchestrates business workflows (`DocumentIngestionService`, `RetrievalService`, `InferenceService`, `NotificationService`).
4. **Domain Core Layer**: Pure models, recursive financial text chunkers (512 char target, 64 overlap), table alignment preserver, citation formatters (`[1] filename, p.X (chunk Y/Z)`), and zero-hallucination policies.
5. **Infrastructure Layer**: Vendor-decoupled adapters for Supabase PostgreSQL (`pgvector`), Supabase Storage, Groq LPU API, OpenRouter fallback, and Resend email.

### 1.2 System Topology Diagram

```text
[Frontend: Next.js 16 / React 19]
      │
      │ HTTPS REST (Documents, Health) & SSE (Real-Time Token Stream)
      ▼
[API Router Layer: FastAPI]
      │
      ▼
[Service Orchestration Layer]
 ├── DocumentIngestionService ──> PyMuPDF C-Engine + SentenceTransformers CPU (384-d)
 ├── RetrievalService         ──> Cosine Similarity Search via match_chunks RPC
 ├── InferenceService         ──> Groq qwen/qwen3.8-27b (Fallback: OpenRouter)
 └── NotificationService      ──> Resend REST API
      │
      ▼
[Domain Core: Pure Invariants, Chunking & Grounding]
      │
      ▼
[Infrastructure Layer: Vendor Decoupled Adapters]
 ├── Supabase PgVector (Postgres 17.6 + vector 0.8.2)
 ├── Supabase Storage (Bucket: documents)
 ├── Groq LPU Engine
 ├── OpenRouter Free Router
 └── Resend Transactional Engine
```

---

## 2. Integrated Technology Stack

| Layer | Selected Technology | Version | Rationale & Why Chosen |
|---|---|---|---|
| **Frontend / UI** | Next.js (App Router), React 19 | 16.x / 19.x | Ultra-fast SSR, modern React Server Components, zero hydration mismatch |
| **Styling & Design**| Tailwind CSS v4 + OKLCH Tokens | v4.x | Wide-gamut colors, native `@theme inline`, dark mode, 5 UI states |
| **State & Cache** | TanStack Query v5 + `useHydrated`| v5.x | Deterministic cache with 5-minute staleTime, zero hydration flash |
| **Backend / API** | Python FastAPI + Uvicorn | 0.115+ | High-throughput asynchronous I/O, typed Pydantic v2 schemas |
| **PDF Extraction** | PyMuPDF (`fitz`) | 1.25+ | Native C-engine extraction, 10x-50x faster than pdfminer, native table parser |
| **Embeddings** | `sentence-transformers` (`all-MiniLM-L6-v2`)| 3.x | Lightweight 384-d dense embeddings, sub-40ms CPU latency, ~120MB RAM |
| **Vector Database**| Supabase PostgreSQL + `pgvector`| 17.6 / 0.8.2| ACID storage, native vector index, transactional metadata consistency |
| **LLM Inference** | Groq LPU (`qwen/qwen3.8-27b`) | API | 300+ tok/s sub-second inference, transparent OpenRouter fallback chain |
| **Notifications** | Resend REST API | API | Zero-overhead transactional alert delivery |

---

## 3. System Invariants & Non-Negotiable Rules

### 3.1 Strict One-Way Dependency Rule
$$\text{Client / Routes} \longrightarrow \text{Services} \longrightarrow \text{Domain Core} \longrightarrow \text{Infrastructure}$$
- Controllers, route handlers, and UI components are strictly forbidden from executing raw database queries or manipulating third-party SDKs directly.
- All operations flow strictly inward to services and domain core.

### 3.2 Vendor Decoupling Seams (Exit Strategy)
- LLM inference and vector storage adhere to abstract base interfaces (`BaseLLMClient`, `BaseVectorStore`).
- Switching LLM or database providers requires modifying exactly 1 adapter file, leaving application core untouched.

### 3.3 Zero-Hallucination Grounding Rule
- If the cosine similarity score of retrieved chunks is below threshold (`0.65`) or facts are absent, the prompt instructs the model to return: *"The provided document does not disclose this information."*
- Every factual statement in the answer must include inline citations `[X]` pointing to verified chunks.

### 3.4 Memory Management & PyMuPDF Cleanup
- Every PDF extraction must wrap document processing in `try...finally:` and invoke `doc.close()` and `fitz.TOOLS.store_shrink(100)` to release MuPDF internal `fz_store` cache.

### 3.5 Vector Index Scan Preservation
- `pgvector` queries must order by `c.embedding <=> query_embedding` directly (never `1 - distance`), preserving the index scan.

### 3.6 Boot-Time Environment Schema Validation
- All required environment variables (`SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `GROQ_API_KEY`, etc.) are strictly validated at application startup using Pydantic `BaseSettings`.

---

## 4. Storage Schema & Entity Relationships

### 4.1 Table: `documents`
- `id`: UUID (Primary Key, default `gen_random_uuid()`)
- `filename`: TEXT NOT NULL
- `page_count`: INTEGER DEFAULT 0
- `chunk_count`: INTEGER DEFAULT 0
- `status`: TEXT DEFAULT 'processing' ('uploaded', 'processing', 'ready', 'error')
- `error_message`: TEXT NULL
- `is_sample`: BOOLEAN DEFAULT FALSE
- `created_at`: TIMESTAMPTZ DEFAULT now()

### 4.2 Table: `chunks`
- `id`: BIGSERIAL PRIMARY KEY
- `document_id`: UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE
- `content`: TEXT NOT NULL
- `source`: TEXT NOT NULL (filename)
- `page`: INTEGER NOT NULL (1-indexed page number)
- `chunk_index`: INTEGER NOT NULL (0-indexed sequence)
- `total_chunks`: INTEGER NOT NULL
- `metadata`: JSONB DEFAULT '{}'::jsonb
- `embedding`: vector(384) NOT NULL

---

## 5. Directory Structure Blueprint

```text
/home/shaikhfardin/Projects/Project 2/
├── backend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── documents.py
│   │   │   │   ├── ask.py
│   │   │   │   └── health.py
│   │   │   └── main.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── errors.py
│   │   ├── domain/
│   │   │   ├── chunker.py
│   │   │   ├── models.py
│   │   │   └── citation.py
│   │   ├── services/
│   │   │   ├── ingestion.py
│   │   │   ├── retrieval.py
│   │   │   └── inference.py
│   │   └── infrastructure/
│   │       ├── supabase_client.py
│   │       ├── groq_client.py
│   │       ├── openrouter_client.py
│   │       └── resend_client.py
│   ├── tests/
│   ├── pyproject.toml
│   └── .env.local
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   └── globals.css
│   │   ├── components/
│   │   │   ├── ui/
│   │   │   ├── chat/
│   │   │   ├── documents/
│   │   │   └── citations/
│   │   ├── lib/
│   │   └── hooks/
│   ├── package.json
│   └── .env.local
└── docs/
    ├── PRD.md
    ├── architecture.md
    ├── api-docs.md
    ├── deployment.md
    └── TEST.md
```
