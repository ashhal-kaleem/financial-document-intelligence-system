# CONTEXT.md — Living Workspace Memory & Active State Tracker

## Current Milestone & Status
- **System**: Financial Document Intelligence System (FDIS)
- **Status**: Production Full-Stack Deployed to Vercel (Serverless Python Backend + Next.js Frontend)
- **Git Commit**: `9da15d3` pushed to `origin/main` on GitHub
- **UI Architecture**: Clean minimal dark mode, permanent Inter font, zero wallpaper background
- **Hosting**: 100% Free Tier, Zero-Card Serverless on Vercel Cloud
- **GitHub Codespaces VM**: SHUT DOWN. Zero VM consumption.
- **Local Machine**: Zero background processes (0% CPU/RAM consumption).

## Production Live URLs (Vercel Serverless)
- **Primary Domain**: [https://financial-doc-ai.vercel.app](https://financial-doc-ai.vercel.app)
- **Alias Domain**: [https://fdis-intelligence.vercel.app](https://fdis-intelligence.vercel.app)
- **Live Health Endpoint**: [https://financial-doc-ai.vercel.app/api/v1/health](https://financial-doc-ai.vercel.app/api/v1/health) (Status: `healthy`, DB: `connected`)
- **Live Documents Endpoint**: [https://financial-doc-ai.vercel.app/api/v1/documents](https://financial-doc-ai.vercel.app/api/v1/documents) (Total: 2 documents indexed)
- **Live RAG Context Endpoint**: `POST https://financial-doc-ai.vercel.app/api/v1/ask/context` (Hugging Face Inference API embeddings + Supabase pgvector)
- **Live SSE Streaming Endpoint**: `POST https://financial-doc-ai.vercel.app/api/v1/ask/stream` (Groq LPU grounded SSE token streaming)

## Refinements Completed in this Turn:
1. **Removed "Visual & Typography Studio" Completely**:
   - Deleted [theme-customizer.tsx](file:///home/shaikhfardin/Projects/Project%202/frontend/src/components/settings/theme-customizer.tsx).
   - Removed the Palette button and modal state from [dashboard-header.tsx](file:///home/shaikhfardin/Projects/Project%202/frontend/src/components/dashboard/dashboard-header.tsx).
   - Removed `activeBackground`, `setActiveBackground`, `activeFont`, `setActiveFont` from [useFDISStore.ts](file:///home/shaikhfardin/Projects/Project%202/frontend/src/store/useFDISStore.ts).
2. **Permanent Clean Inter Typography**:
   - Set font permanently to `Inter` (`font-sans`) loaded self-hosted via `next/font/google` in [layout.tsx](file:///home/shaikhfardin/Projects/Project%202/frontend/src/app/layout.tsx).
   - Cleaned [page.tsx](file:///home/shaikhfardin/Projects/Project%202/frontend/src/app/page.tsx) of all dynamic font conditionals.
3. **Removed Ambient Wallpaper Backgrounds**:
   - Removed Unsplash/Pexels image backgrounds (`hero-bg.jpg`, `wallstreet.jpg`) and overlay layers from [page.tsx](file:///home/shaikhfardin/Projects/Project%202/frontend/src/app/page.tsx).
   - Background is now a pristine, modern dark surface (`bg-background text-foreground`).
4. **Deployed & Synced**:
   - Tested zero TypeScript errors via `npx tsc --noEmit`.
   - Verified 100% Playbook compliance with `verify-playbook.py` (0 warnings).
   - Committed and pushed to `main` on GitHub (`9da15d3`).
   - Deployed live to Vercel production.

### UI Hardening & TypeError Resolution (fb7300a)
- **Root Cause**: `DocumentSidebar` and `page.tsx` lacked fallback defense for `documents` prop when resolving initial query state during SSR/early mount, leading to `TypeError: Cannot read properties of undefined (reading 'length')`. In addition, hot reloading with deleted theme components left stale webpack chunk references in `.next`.
- **Resolution**:
  1. Defaulted `documents = []` in [document-sidebar.tsx](file:///home/shaikhfardin/Projects/Project%202/frontend/src/components/documents/document-sidebar.tsx) and wrapped array calculations with safe `(documents?.length ?? 0)` and `safeDocs.length`.
  2. Guarded `documents` in [page.tsx](file:///home/shaikhfardin/Projects/Project%202/frontend/src/app/page.tsx) with `safeDocs = documents || []`.
  3. Cleared `.next` build cache. Verified zero TypeScript errors (`tsc --noEmit`). Verified 100% Playbook Invariants via `verify-playbook.py`.
  4. Pushed commit `fb7300a` to GitHub main for auto-deployment to Vercel.

### RAG Document Intelligence Prompt Enhancement (080a860)
- **Problem**: When users uploaded non-corporate 10-K documents (e.g. college engineering project synopses) and asked general questions like "isko read karo", the LLM correctly extracted the context but prepended a rigid refusal ("The provided financial document does not disclose this information... not a corporate annual report or 10-K").
- **Root Cause**: Hardcoded `GROUNDED_SYSTEM_PROMPT` in `citation.py` and `user_prompt` in `inference.py` strictly limited scope to 10-K/balance sheets and mandated the phrase "The provided financial document does not disclose this information".
- **Fix**:
  1. Updated `GROUNDED_SYSTEM_PROMPT` in `backend/src/domain/citation.py` and `frontend/api/src/domain/citation.py` to act as an advanced Document Intelligence AI that analyzes, summarizes, and answers questions on *any* document while retaining strict grounding and exact `[1]`, `[2]` citations.
  2. Updated `user_prompt` in `backend/src/services/inference.py` and `frontend/api/src/services/inference.py` to explicitly fulfill requests to read, explain, and summarize uploaded documents.
  3. Committed and pushed commit `080a860` to GitHub `main`.

### Resolution of Hardcoded Values & Critical PDF Linkage Bug
- **Audit Findings**: Deep inspection identified 16 hardcoded areas across frontend and backend, including a critical bug where citations failed to load PDFs in the modal viewer due to missing `documentId`, static Apple FY24 data in statements/comparison/memo exports, fake dashboard KPIs, and hardcoded storage buckets.
- **Key Changes Implemented**:
  1. **Citation & PDF Viewer Linkage**: Added `documentId` to `Citation` interface in `store/useFDISStore.ts`, mapped `documentId` from backend citations in `components/chat/chat-interface.tsx`, and passed it through `components/citations/citation-drawer.tsx` and `components/chat/chat-message-item.tsx` to `openPdfViewer()`, eliminating the blank viewer bug.
  2. **Removed Silent Apple Sample Fallback**: In `backend/src/api/routes/documents.py`, removed the fallback that silently served `tests/sample_apple_10k.pdf` when storage retrieval failed, ensuring proper 404 reporting for user filings.
  3. **Dynamic Views & Exports**: Bound `financial-statements-grid.tsx`, `filing-comparison-view.tsx`, and `memo-export-modal.tsx` to the active user-uploaded documents and real timestamps instead of static Apple mock data.
  4. **Dynamic Dashboard KPIs**: Replaced fake `$218B` / `1.2s` metrics in `kpi-strip.tsx` with live counts of uploaded documents, ready status, and total pgvector chunks.
  5. **Dynamic Chat Header & Offline Avatars**: Made assistant model badge in `chat-message-item.tsx` reflect the selected model (GPT-4o vs Claude 3.5 Sonnet) and switched avatars to offline SVG icons.
  6. **Backend Infrastructure Hardening**: Made Supabase storage bucket dynamic via `settings.SUPABASE_STORAGE_BUCKET`, added `MAX_UPLOAD_SIZE_BYTES` and `ALLOWED_EXTENSIONS` to `core/config.py`, and standardized the response envelope in `/api/v1/notify`.
- **Verification**:
  - Frontend: `pnpm run typecheck` (0 errors).
  - Backend: `uv run --python 3.12 pytest -v` (15 passed, 0 failed).
  - Playbook verification: `verify-playbook.py` passed with 0 warnings.
