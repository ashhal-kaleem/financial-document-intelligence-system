# CONTEXT.md — Living Workspace Memory & Active State Tracker

## Current Milestone & Status
- **System**: Financial Document Intelligence System (FDIS)
- **Status**: Live in GitHub Codespaces (Cloud VM execution, Zero Laptop Load)
- **Git Commit**: `1d6965b` pushed to `origin/main` on GitHub
- **Local Machine**: Zero laptop load (0% CPU/RAM consumption).

## Changes Implemented & Verified in this Turn
1. **Fixed PDF Reading / RAG Chunk Retrieval**:
   - Diagnosed root cause: Cosine similarity threshold was set too strictly (`0.40`), filtering out valid embedding matches (which score ~0.15 - 0.35).
   - Lowered default `SIMILARITY_THRESHOLD` to `0.05` and added an adaptive zero-threshold fallback in `RetrievalService` so questions about uploaded filings always retrieve the top relevant passages with exact citations and page numbers.
   - Live probe to `/api/v1/ask/context` verified 5 chunks returned with citations.
2. **Removed Groq API Mentions**:
   - Removed "Zero Groq Limits" badge in `chat-input-box.tsx`, replaced with `Puter AI Copilot`.
3. **Direct Document Upload Inside Chat**:
   - Added direct file upload button (`Paperclip` icon) in `ChatInputBox` with automatic document indexing and TanStack Query cache invalidation.
   - Added direct upload button in `ChatEmptyState`.
4. **Completely Removed API Intelligence Hub**:
   - Deleted `frontend/src/components/settings/api-hub-modal.tsx`.
   - Removed CPU icon button and state from `DashboardHeader` and `useFDISStore`.
   - Removed component from `Home` in `page.tsx`.

## Active Cloud Endpoints (GitHub Codespace: `shiny-tribble-wrrgx46wv5wvf9999`)
- **Frontend App**: `https://shiny-tribble-wrrgx46wv5wvf9999-3000.app.github.dev` (HTTP 200 OK)
- **Backend API**: `https://shiny-tribble-wrrgx46wv5wvf9999-8000.app.github.dev` (HTTP 200 OK)
- **Healthcheck**: `https://shiny-tribble-wrrgx46wv5wvf9999-8000.app.github.dev/api/v1/health` (Healthy)
