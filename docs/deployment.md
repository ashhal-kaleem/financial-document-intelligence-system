# Deployment & Production Runbook — Financial Document Intelligence System (FDIS)

> **Status**: Approved  
> **Master Protocol**: `/home/shaikhfardin/templates/instructions.md`  
> **Last Updated**: 2026-09-06

---

## 1. Environment Architecture

- **Frontend**: Next.js 16 (App Router) on Vercel or Docker container.
- **Backend API**: FastAPI asynchronous server running via Uvicorn.
- **Vector Database**: Supabase PostgreSQL 17.6 with `pgvector 0.8.2` (Mumbai `ap-south-1`).
- **Object Storage**: Supabase Storage (`documents` bucket).
- **Inference Engines**: Groq LPU (`qwen/qwen3.8-27b`) with OpenRouter transparent fallback.

---

## 2. Environment Variables & Secret Configuration

### Backend (`backend/.env.local` / Environment)
```env
SUPABASE_URL=https://aluzqooagiymysssnhkg.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
SUPABASE_STORAGE_BUCKET=documents
GROQ_API_KEY=your_groq_key
GROQ_MODEL=qwen/qwen3.8-27b
OPENROUTER_API_KEY=your_openrouter_key
OPENROUTER_DEFAULT_MODEL=liquid/lfm-2.5-2.6b:free
RESEND_API_KEY=your_resend_key
PORT=8000
```

### Frontend (`frontend/.env.local` / Environment)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## 3. Local Development Runbook

### Backend (Python via `uv`)
```bash
cd backend
uv sync
uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend (Next.js via `pnpm`)
```bash
cd frontend
pnpm install
pnpm dev
```

---

## 4. Pre-Flight Production Checklist & Audit

- [ ] Run backend tests: `cd backend && uv run pytest -v`
- [ ] Run frontend typecheck: `cd frontend && pnpm run typecheck`
- [ ] Client Secret Leak Audit:
  ```bash
  grep -rn "API_KEY\|SERVICE_ROLE\|SECRET" frontend/src/ 2>/dev/null | grep -v "NEXT_PUBLIC_"
  ```
  Ensure zero private backend secrets exist in frontend client code.
