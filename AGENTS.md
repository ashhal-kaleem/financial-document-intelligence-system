# AGENTS.md

> **Master Agent Handbook & Developer Guide for Financial Document Intelligence System (FDIS)**  
> This file is the single source of truth for all AI agents, pair programmers, and contributors.  
> Built on the Master Sovereign Developer Protocol (`/home/shaikhfardin/templates/instructions.md`).

---

## 🧭 System Overview & Architecture Summary
- **Domain**: Enterprise Financial Document Intelligence, Corporate PDF RAG, Balance Sheet & Footnote Q&A.
- **Core Architecture**: 4-Tier Clean Architecture (FastAPI Backend + Next.js 16 / React 19 Frontend).
- **Detailed Specs**: Read `docs/architecture.md`, `docs/PRD.md`, and `docs/api-docs.md`.
- **Active Memory & Progress**: Read `CONTEXT.md` before starting work; update it before completing any session.
- **Systematic Feature Delivery**: Follow `systematic-build.md` for all phased delivery.

---

## 📁 Repository Layout & Invariants

```text
/home/shaikhfardin/Projects/Project 2/
├── docs/                      # PRD, Architecture, API contracts, Deployment, TEST
├── backend/                   # Python FastAPI 4-Tier Backend Engine
│   ├── src/
│   │   ├── api/               # API Routes (/documents, /ask/stream, /health)
│   │   ├── core/              # Config, Error handling, Settings
│   │   ├── domain/            # Pure domain models, recursive chunker, citations
│   │   ├── services/          # Business logic (Ingestion, Retrieval, Inference)
│   │   └── infrastructure/    # Supabase (pgvector/storage), Groq, OpenRouter, Resend
│   ├── tests/                 # Unit & contract tests
│   ├── pyproject.toml         # Python package & dependency definition
│   └── .env.local             # Local backend secrets
├── frontend/                  # Next.js 16 + React 19 + Tailwind v4 OKLCH Frontend
│   ├── src/
│   │   ├── app/               # Next.js App Router pages & layouts
│   │   ├── components/        # UI primitives, chat stream, document drawer, citation inspector
│   │   ├── lib/               # Utilities, API client
│   │   └── hooks/             # Custom hooks (SSE consumer, TanStack Query)
│   ├── package.json
│   └── .env.local
├── AGENTS.md                  # This file
├── CONTEXT.md                 # Living workspace memory & state tracker
├── systematic-build.md        # Atomic verification checklist
└── CHANGELOG.md               # Version history
```

### 🏛️ Core Architectural & Security Invariants
1. **Strict One-Way Dependency Flow**:
   $$\text{Client / Routes} \longrightarrow \text{Services} \longrightarrow \text{Domain Core} \longrightarrow \text{Infrastructure}$$
2. **Vendor Decoupling Seams**: LLM and vector clients sit behind abstract interfaces (`BaseLLMClient`, `BaseVectorStore`).
3. **Zero-Hallucination Policy**: If retrieval score < threshold or facts are absent, return explicit non-disclosure notice.
4. **PyMuPDF Memory Safety**: Wrap extractions in `try...finally` with `doc.close()` and `fitz.TOOLS.store_shrink(100)`.
5. **No Secret Leakage**: Zero server secrets in client code or Git repository.
6. **Deep Live Diagnostic Healthchecks**: Endpoints under `/api/health` must execute a real live query probe (e.g. `SELECT 1` or ping with timeout) and return HTTP 503 if any critical dependency is down. Merely checking if an environment variable string exists is strictly forbidden.
7. **Zero Raw UI Primitives**: Hand-crafting raw `<button>`, `<input>`, or un-styled controls directly inside feature components is strictly forbidden. Primitives MUST be scaffolded in `components/ui/` first and imported from `@/components/ui/*`.

### 🛡️ Non-Negotiable Full-Stack Playbook Invariants (Law of Quality)
Every component in FDIS must strictly follow the companion playbooks (`templates/playbooks/`):

#### 🐍 Backend Invariants (`playbooks/backend/`):
1. **Unified Response Envelopes (`00 & 01`)**:
   - Every HTTP endpoint must return a standard envelope:
     - Success: `{"success": true, "data": {...}, "meta": {"timestamp": "...", "requestId": "..."}}`
     - Error: `{"success": false, "error": {"code": "...", "message": "...", "details": [...]}, "meta": {"timestamp": "...", "path": "..."}}`
   - Never return raw ORM models, un-enveloped lists, or bare dicts (`return doc` is strictly prohibited).
   - Global exception handlers must catch domain errors, HTTP exceptions, and `RequestValidationError` (422) in the standard envelope.
2. **Resilient LLM Routing (`04`)**:
   - Cloud LLM clients must never hardcode a single model string; pass an ordered `models` fallback array (e.g. OpenRouter `models: [primary, fallback_1, fallback_2]`).
3. **SSE Disconnect Defense (`04`)**:
   - Every SSE streaming endpoint must inject the request object and check `if await request.is_disconnected(): break` on every token yield to immediately terminate upstream computation when clients disconnect.
4. **Non-Blocking Background Ingestion (`00 & 05`)**:
   - Operations taking >200ms (PDF parsing, OCR, chunking, vector embeddings) must never block the HTTP route thread. Return `HTTP 202 Accepted` with a job/document ID and execute via `BackgroundTasks` or async task queues.
5. **Deterministic Database Transactions (`02 & 06`)**:
   - Zero raw SQL without migrations. Tests must use transactional rollbacks leaving zero database residues.

#### 🎨 Frontend Invariants (`playbooks/frontend/`):
1. **Strict State Ownership Boundary (`00 & 07`)**:
   - **Server State**: Managed exclusively by TanStack Query v5 (`useQuery`, `useMutation`).
   - **Client UI State**: Managed by Zustand stores in `src/store/` (`useFDISStore`).
   - Prop-drilling UI state across more than 1 parent-child level is strictly prohibited.
2. **Standard Component Registries (`03`)**:
   - All UI building blocks must live in `components/ui/` using accessible shadcn/ui primitives.
   - Hand-crafting raw `<button>` or un-styled interactive primitives inside feature components is strictly prohibited.
3. **Tabular Numerals & Spatial Rhythm (`01 & 05`)**:
   - All financial numbers, counters, timestamps, and percentages must include `tabular-nums` to eliminate layout jitter.
   - Enforce the 8-point spatial rhythm (`p-6` cards, `px-3.5 py-2` buttons).
4. **The 5 Mandatory UI States (`01`)**:
   - Every data component must handle all 5 states: Ideal, Loading (Skeleton mirror, never generic spinners), Empty (graphic + CTA), Error (explanation + Retry action), and Degraded.
5. **Tactile Micro-Interactions (`01`)**:
   - Button click compression (`active:scale-[0.98]`), card hover lift, and smooth state transitions.

- **Mandatory Compliance Verification Command**:
  Execute before any phase or milestone sign-off:
  `python3 /home/shaikhfardin/templates/scripts/verify-playbook.py .`
  Zero violations permitted.

---

## ☁️ Cloud Development & GitHub Codespaces Policy (Zero-Laptop Load)

For resource-constrained or low-spec local laptops (preventing CPU throttling, RAM exhaustion, and battery drain), this repository is fully configured for cloud execution via **GitHub Codespaces**:

- **One-Click Cloud Launch**: Navigate to `https://codespaces.new/Fardin7798/financial-document-intelligence-system?quickstart=1` (or click **Code -> Codespaces -> Create codespace on main** in GitHub).
- **GitHub CLI Launch**:
  ```bash
  gh codespace create -r Fardin7798/financial-document-intelligence-system --machine standardLinux32gb
  ```
- **Autonomous Zero-Git Background Sync (`./dev-sync.sh`)**:
  - The agent runs `./dev-sync.sh` as a background daemon process. Every keystroke/save in Antigravity IDE auto-syncs to Cloud Codespace in 1 second without `git push`.
- **Automatic Cloud Configuration**:
  - Defined in `.devcontainer/devcontainer.json`.
  - Exposes port `3000` (Frontend) and `8000` (Backend) with auto-HTTPS port forwarding.
  - Automatically runs background installation (`uv sync` and `pnpm install`) on boot via `postCreateCommand`.
- **Laptop Resource Benefit**: Local machine CPU and RAM usage remains near 0%; all builds, dev servers, and heavy tests execute in the cloud VM.

---

## ⚡ Mandatory Terminal Commands & Operations Policy

- **Run Backend**: `cd backend && uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload`
- **Run Frontend**: `cd frontend && pnpm dev`
- **Test Backend**: `cd backend && uv run pytest -v`
- **Typecheck Frontend**: `cd frontend && pnpm run typecheck`
- **Check Secrets**: `grep -rn "API_KEY\|SERVICE_ROLE\|SECRET" frontend/src/ 2>/dev/null | grep -v "NEXT_PUBLIC_"`
