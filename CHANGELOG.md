# Changelog

All notable changes to the Financial Document Intelligence System (FDIS) are documented here.

## [1.0.0] - 2026-09-06
### Added
- **4-Tier Clean Architecture**: Decoupled routers, services, domain core, and infrastructure adapters.
- **Native C-Engine PDF Parsing**: PyMuPDF with table extraction and automatic `store_shrink(100)` memory cache release.
- **Recursive Financial Chunker**: 512-character target with 64-character overlap preserving table rows and footnotes.
- **Dense Vector Embedding Pipeline**: `all-MiniLM-L6-v2` generating 384-dimensional normalized vectors on CPU.
- **Supabase pgvector RPC**: Optimized `match_chunks` stored procedure supporting document filters and cosine similarity.
- **Dual-Engine Inference with Failover**: Groq LPU (`qwen/qwen3.8-27b`) with automatic quota-shifting to OpenRouter free router.
- **Real-Time SSE Streaming**: Token-by-token streaming endpoint on `/api/v1/ask/stream`.
- **Next.js 16 + React 19 + Tailwind CSS v4 Frontend**:
  - Wide-gamut OKLCH theme tokens and sleek dark mode.
  - TanStack Query v5 with `useHydrated` guard for zero hydration flash.
  - Document sidebar with progress bar and filing index.
  - Main chat interface with 5 UI states (Ideal, Empty, Skeleton, Error with retry, Partial).
  - Slide-out Citation Inspector Drawer displaying page numbers, similarity gauges, and source snippets.
  - Transactional email audit alert delivery via Resend API.
