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

### Integration of Luxury Roasted Espresso & Dusty Rose Color Palette
- **Palette Tokens**:
  - `#2A0800` (Dark Espresso Black-Brown): Registered as `--background` and `--sidebar`.
  - `#775144` (Medium Mocha / Coffee Brown): Registered as `--card`, `--secondary`, and `--popover`.
  - `#C09891` (Dusty Rose / Mauve Brown): Registered as `--primary`, `--ring`, and `--accent`.
  - `#BEA8A7` (Light Grayish Mauve): Registered as `--muted-foreground`, `--border`, and `--input`.
  - `#F4DBD8` (Blush Porcelain / Light Pinkish White): Registered as `--foreground` and `--card-foreground`.
- **Text & Font Contrast Audit**:
  - Rechecked all TSX components for font legibility: Verified `14.09:1` AAA contrast for main text, `8.25:1` AAA contrast for muted text, and `7.18:1` AAA contrast for primary button text.
  - Replaced lingering raw `emerald` classes in `auth-modal.tsx`, `memo-export-modal.tsx`, and `chat-input-box.tsx` with semantic `text-primary` tokens.
  - Updated `BorderBeam` in `page.tsx` with dusty rose / mocha gradient.
- **Verification**:
  - `pnpm run typecheck` (0 errors).
  - `pnpm run build` (Static 6/6 pages generated cleanly in 38s).
  - `verify-playbook.py` (0 warnings).

### Light Sandstone (#DCD7D5) & Editorial Mocha Palette Migration
- **User Preference**: Switched from dark background to light sandstone background (`#DCD7D5`) to eliminate heavy darkness while maintaining visual elegance.
- **Palette Mapping**:
  - `--background`: `oklch(0.885 0.008 43)` (`#DCD7D5` Light Sandstone Alabaster canvas).
  - `--sidebar`: `oklch(0.865 0.01 43)` (`#DCD7D5` Sandstone surface).
  - `--foreground`: `oklch(0.20 0.06 40)` (`#2A0800` Deep Espresso text, achieving 12.99:1 WCAG AAA contrast).
  - `--card` / `--popover`: `oklch(0.985 0.004 40)` (Crisp warm white elevated surface, achieving 15.5:1 WCAG AAA contrast).
  - `--primary`: `oklch(0.36 0.055 40)` (Rich Mocha/Espresso primary action button) with `--primary-foreground`: `oklch(0.985 0.004 40)`.
  - `--secondary`: `oklch(0.92 0.015 30)` (`#F4DBD8` Soft blush surface).
  - `--muted`: `oklch(0.91 0.01 40)` & `--muted-foreground`: `oklch(0.46 0.04 40)` (Mocha midtone for secondary labels, 5.0:1 AA contrast).
  - `--border`: `oklch(0.50 0.03 40 / 18%)` (Soft sand outline).
- **Component Polish & Contrast Hardening**:
  - `chat-message-item.tsx`: Removed `prose-invert` so rendered markdown text, bold, and headings display in deep espresso rather than washed-out white.
  - `dialog.tsx`: Upgraded modal content to `bg-card text-card-foreground` so modals stand out distinctly with warm white surfaces against dimmed backdrops.
  - `financial-statements-grid.tsx` & `filing-comparison-view.tsx`: Upgraded financial delta indicators from light green/pink to high-contrast `text-emerald-700` and `text-rose-700`.
  - `auth-modal.tsx` & `memo-export-modal.tsx`: Refined warning and auxiliary icons to high-contrast dark tones (`text-amber-800`, `text-purple-700`).
  - `page.tsx`: Adjusted `BorderBeam` glow gradient to mocha (`oklch(0.36 0.055 40)`) and dusty rose (`oklch(0.72 0.05 30)`) with 25% opacity.
- **Verification**:
  - `pnpm run typecheck` (0 errors).
  - `pnpm run build` (6/6 static pages compiled cleanly in 7.7s).
  - `python3 verify-playbook.py .` (0 warnings).

### Milestone: Financial 3D Perspective Cards Integration
- Created [3d-card.tsx](file:///home/shaikhfardin/Projects/Project%202/frontend/src/components/ui/3d-card.tsx) primitive (`CardContainer`, `CardBody`, `CardItem`, `useMouseEnter`).
- Implemented [financial-3d-cards.tsx](file:///home/shaikhfardin/Projects/Project%202/frontend/src/components/financials/financial-3d-cards.tsx) dedicated to FDIS financial metrics:
  - **Net Profit (FY24)**: `$93.74B` (+12.4% YoY)
  - **Debt-to-Equity**: `0.64x` (Conservative Leverage)
  - **Operating Cash Flow**: `$108.81B` (+16.2% YoY)
- Replaced generic demo in [3d-card-demo-2.tsx](file:///home/shaikhfardin/Projects/Project%202/frontend/src/components/3d-card-demo-2.tsx) with Financial 3D Cards.
- Embedded `<Financial3DCards />` live into [financial-statements-grid.tsx](file:///home/shaikhfardin/Projects/Project%202/frontend/src/components/financials/financial-statements-grid.tsx).
- Invariant audits verified: `tsc --noEmit` passed (0 errors), `verify-playbook.py` passed (0 warnings), strictly < 150 lines (131 lines).

### Milestone: NumberTicker Component Direct Replacement & Invariant Verification
- Created [number-ticker.tsx](file:///home/shaikhfardin/Projects/Project%202/frontend/src/components/ui/number-ticker.tsx) with spring physics (`damping: 60`, `stiffness: 100`), `tabular-nums`, and Intl currency formatting support.
- Fully replaced static metrics in [financial-3d-cards.tsx](file:///home/shaikhfardin/Projects/Project%202/frontend/src/components/financials/financial-3d-cards.tsx) and [3d-card-demo-2.tsx](file:///home/shaikhfardin/Projects/Project%202/frontend/src/components/3d-card-demo-2.tsx) with dynamic `<NumberTicker />` on load:
  * Net Profit: `$0.00B` -> `$93.74B`
  * Debt-to-Equity: `0.00x` -> `0.64x`
  * Operating Cash Flow: `$0.00B` -> `$108.81B`
  * YoY Variance: `0.0%` -> `+12.4% YoY` / `+16.2% YoY`
- Integrated `<NumberTicker />` directly into [financial-statements-grid.tsx](file:///home/shaikhfardin/Projects/Project%202/frontend/src/components/financials/financial-statements-grid.tsx) for all balance sheet line items (FY24, FY23, YoY %).
- Created [number-ticker-demo.tsx](file:///home/shaikhfardin/Projects/Project%202/frontend/src/components/ui/number-ticker-demo.tsx) exhibiting `$124.5M` and `+14.2% YoY` smoothly counting up.
- Audit & Verification: `tsc --noEmit` passed (0 errors), `verify-playbook.py` passed (0 warnings), strictly < 150 lines (136 lines).

### Milestone: BentoGrid Component Direct Replacement
- Installed `@tabler/icons-react` and `motion` dependencies.
- Added [bento-grid.tsx](file:///home/shaikhfardin/Projects/Project%202/frontend/src/components/ui/bento-grid.tsx) primitive.
- Directly replaced [financial-statements-grid.tsx](file:///home/shaikhfardin/Projects/Project%202/frontend/src/components/financials/financial-statements-grid.tsx) in-place with `BentoGridThirdDemo` (zero wrappers).
- All 14 Playbook Invariants verified (`verify-playbook.py` passed with 0 warnings).
- TypeScript verification passed with 0 errors (`tsc --noEmit`).
