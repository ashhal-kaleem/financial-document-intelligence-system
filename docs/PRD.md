# Product Requirements Document (PRD) — Financial Document Intelligence System (FDIS)

> **Status**: Approved  
> **Target Release**: v1.0 (Production-Grade MVP)  
> **Approved Architecture Approach**: Approach 3 (Pragmatic Enterprise 4-Tier Clean Architecture)  
> **Master Protocol**: `/home/shaikhfardin/templates/instructions.md`  
> **Last Updated**: 2026-09-06

---

## 1. Executive Summary & Problem Definition

### 1.1 Purpose
The **Financial Document Intelligence System (FDIS)** is an enterprise-grade AI research assistant tailored for corporate financial analysts, auditors, and institutional investors to ingest complex corporate annual reports (PDFs) and perform sub-second, strictly grounded Q&A with verifiable page-level citations and real-time streaming inference.

### 1.2 Problem Statement
Corporate 10-K, 10-Q, and annual reports are dense, multi-hundred-page documents filled with complex balance sheets, debt maturity schedules, footnotes, and nuanced risk disclosures. Financial analysts spend 4–8 hours per filing manually searching for critical metrics, while generic LLMs hallucinate numbers or cite fabricated pages. FDIS eliminates hallucination through recursive financial chunking, dense vector similarity matching in `pgvector`, and deterministic zero-hallucination guardrails.

### 1.3 Target Audience & ICP (Ideal Customer Profile)
- **Primary ICP**: Corporate Financial Analysts, Audit Professionals, Equity Research Associates, and M&A Due Diligence teams analyzing corporate earnings, balance sheets, and audit notes.
- **Value Proposition**: 10x faster financial document review with zero hallucination, sub-second token streaming, table structure preservation, and exact clickable citations `[1] filename, p.X (chunk Y/Z)`.

### 1.4 Goals (What Success Looks Like)
- **Sub-Second Streaming**: Time-to-First-Token (TTFT) < 600ms on Groq LPU `qwen/qwen3.8-27b` with transparent OpenRouter fallback.
- **Strict Grounding & Zero Hallucination**: 100% adherence to source filings; if a metric is omitted from the PDF, the engine explicitly reports non-disclosure.
- **Verifiable Page-Level Citations**: Every claim links back to exact page numbers and chunk offsets in the original document.
- **Robust Table Handling**: Preserve row and column semantics in corporate financial statements.

### 1.5 Non-Goals (Explicitly Out of Scope)
- Automated execution of stock trades or brokerage integrations.
- Modifying or signing official PDF filings.
- Autonomous speculative investment advice or price prediction.

---

## 2. Unit Economics & Pricing Model

$$\text{Estimated Monthly API Cost / Active User} \ll \text{Target Subscription Price}$$

| Metric | Target / Assumption | Calculation / Math |
|---|---|---|
| **Target Pricing Tier** | `$79 / month / analyst` | Standard B2B financial research seat |
| **Est. Daily Usage** | `25 queries / analyst / day` | ~750 queries per active month |
| **Ingestion Cost** | `$0.00` | Native C-engine PyMuPDF + local CPU `all-MiniLM-L6-v2` |
| **Cost Per Query / Call**| `$0.000` | Free tier Groq LPU (14,400 RPD) / OpenRouter free models |
| **Database & Storage** | `$0.00` | Supabase free tier (500MB DB, 1GB Storage for ~50,000 chunks) |
| **Monthly Variable Cost**| `< $0.50 / user / month` | Supabase bandwidth & connection overhead |
| **Gross Margin Target** | `> 99%` | Highly profitable sovereign unit economics |

---

## 3. Target Users & Personas

| Persona Name | Role / Description | Primary Goal | Key Frustration / Need |
|---|---|---|---|
| **Senior Equity Analyst** | Equity Research & Buy-Side Due Diligence | Rapidly cross-reference debt covenants and segment revenues | Wasting hours searching PDF text; hallucinated numbers |
| **Corporate Auditor** | Statutory Audit & Risk Review | Validate footnotes against reported balance sheet numbers | Unverifiable AI summaries lacking page citations |
| **Portfolio Manager** | Asset Management | Compare capital expenditure and guidance across peers | Slow tools, lack of table preservation |

---

## 4. Prioritized User Journeys & Acceptance Scenarios

### 🌟 Priority P1: Core MVP (Mandatory for First Release)

#### User Story 1.1: High-Speed Corporate PDF Ingestion & Chunking
- **As a**: Financial Analyst
- **I want to**: Upload multi-page corporate annual reports or balance sheets (PDF)
- **So that**: The system extracts text, preserves financial tables, generates embeddings, and indexes chunks for instant search.
- **Independent Test**: Upload a multi-page PDF via `POST /api/v1/documents`, verify status transition `uploaded` $\to$ `processing` $\to$ `ready`, and confirm chunks populated in `chunks` table.
- **Acceptance Criteria**:
  - **Scenario A (Happy Path)**:
    - **Given** an authenticated user on the dashboard
    - **When** they drag-and-drop or select a corporate PDF (e.g. 5–50 pages)
    - **Then** upload progress bar animates to 100%, PyMuPDF parses pages, generates 384-d vectors, inserts rows into Supabase `chunks`, and marks status `ready`.
  - **Scenario B (Invalid File / Malformed PDF)**:
    - **Given** an unsupported file type or corrupted PDF
    - **When** user attempts upload
    - **Then** system displays actionable error ("Invalid PDF structure"), cleans temporary buffers, and keeps system state stable.

#### User Story 1.2: Grounded Q&A with Real-Time Token Streaming & Citations
- **As a**: Financial Analyst
- **I want to**: Query specific financial metrics (e.g. "What was the operating margin in 2024?")
- **So that**: I receive a real-time streamed answer with verifiable page citations.
- **Acceptance Criteria**:
  - **Scenario A (Grounded Retrieval)**:
    - **Given** an indexed document with financial metrics
    - **When** the user asks about disclosed figures
    - **Then** the system retrieves top chunks via cosine similarity (`match_chunks`), streams tokens via SSE, and appends citations formatted as `[1] filename, p.X (chunk Y/Z)`.
  - **Scenario B (Zero-Hallucination Non-Disclosure)**:
    - **Given** an indexed document that does not disclose an undisclosed metric (e.g. "What is the CEO's personal home address?")
    - **When** the user asks for that metric
    - **Then** the model responds: *"The provided document does not disclose this information."* without speculating.

---

### 🚀 Priority P2: Key Enhancements (Second Phase)

#### User Story 2.1: Document Management & Drawer Citation Preview
- **As a**: Financial Analyst
- **I want to**: Click on a citation badge in the chat window
- **So that**: A citation inspector drawer opens displaying the exact source snippet, page number, and chunk metadata.

#### User Story 2.2: Multi-Model Fallback & Status Telemetry
- **As a**: Financial Analyst / Operator
- **I want to**: Seamlessly receive answers even if Groq experiences temporary rate limits (429)
- **So that**: OpenRouter transparently fulfills the request with zero user disruption.

---

## 5. Quality Bar & Eval Criteria (Zero-Tolerance Ship Blockers)

- **Zero-Tolerance Hallucinations**: 0% fabricated numbers or citations on test evaluation set.
- **Streaming Latency**: TTFT < 600ms target; hard ceiling < 1200ms.
- **Table Integrity**: Table rows and columns extracted with preserved cell alignment.
- **Memory Safety**: Clean up PyMuPDF cache via `fitz.TOOLS.store_shrink(100)` to prevent daemon RSS memory growth.

---

## 6. Technical Constraints & Verified Dependencies

| Dependency / Service | Purpose | Fallback / Alternative | Verification Status |
|---|---|---|---|
| **Supabase Postgres + pgvector** | Vector similarity & relational metadata | Local SQLite + vector extension | ✅ Verified (Postgres 17.6, pgvector 0.8.2) |
| **Supabase Storage** | Document PDF persistence (`documents` bucket) | Local disk storage (`data/uploads`) | ✅ Verified |
| **Groq AI Engine** | Sub-second LPU inference (`qwen/qwen3.8-27b`) | OpenRouter free models | ✅ Verified |
| **OpenRouter Free Router** | Transparent fallback LLM engine | Graceful queue notice | ✅ Verified |
| **Resend REST API** | Audit alerts and email notifications | Local logger | ✅ Verified |
