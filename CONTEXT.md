# CONTEXT.md — Living Workspace Memory & Active State Tracker

## Current Milestone & Status
- **System**: Financial Document Intelligence System (FDIS)
- **Status**: Live in GitHub Codespaces (Cloud VM execution, Zero Laptop Load)
- **Git Commit**: `3ad6f91` pushed to `origin/main` on GitHub
- **Local Machine**: Zero laptop load (0% CPU/RAM consumption).

## Refinements Implemented & Verified in this Turn
1. **Removed Duplicate Upper Upload Button**:
   - Removed the `Plus` upload button from `sidebar-header.tsx`.
   - Removed `DocumentUploadZone` expansion from `document-sidebar.tsx`.
   - The document upload capability is now exclusively centralized directly inside the chat interface (via the attachment/paperclip button in `ChatInputBox` and the empty-state button).
2. **Removed Tag/Badge from Chat Input**:
   - Completely deleted the tag/badge ("Puter AI Copilot" / formerly "Zero Groq Limits") from `chat-input-box.tsx`. The model selection bar is now 100% clean and tag-free.

## Active Cloud Endpoints (GitHub Codespace: `shiny-tribble-wrrgx46wv5wvf9999`)
- **Frontend App**: `https://shiny-tribble-wrrgx46wv5wvf9999-3000.app.github.dev` (HTTP 200 OK)
- **Backend API**: `https://shiny-tribble-wrrgx46wv5wvf9999-8000.app.github.dev` (HTTP 200 OK)
- **Healthcheck**: `https://shiny-tribble-wrrgx46wv5wvf9999-8000.app.github.dev/api/v1/health` (Healthy)

### Update 2026-09-06: Resolved Document Scoping in RAG Retrieval
- **Problem**: When multiple documents exist in pgvector (e.g. 3,079-chunk Annual Report vs. 24-chunk Project Synopsis), un-scoped queries across the entire database biased toward the 3,079 chunks, returning irrelevant banking passages for queries on the newly uploaded document.
- **Root Cause**: `fetchAskContext` was called without `document_ids`, and `useFDISStore` lacked `selectedDocument` state.
- **Resolution**:
  1. Added `selectedDocument` state and `setSelectedDocument` in `useFDISStore.ts`.
  2. Updated `chat-input-box.tsx` to automatically set `selectedDocument` on PDF upload, and added scope badge with clear toggle.
  3. Updated `chat-interface.tsx` to pass `targetDocIds` (`[selectedDocument.id]`) to `fetchAskContext` and fallback `streamQuestion`.
  4. Updated `document-list-item.tsx` and `document-sidebar.tsx` with visual active target indicator and "All Filings" switcher.
