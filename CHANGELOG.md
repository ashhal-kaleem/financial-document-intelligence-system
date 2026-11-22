> Historical planning/status record. For current implementation and open gates see README.md and docs/production-readiness.md. Old verification and feature claims below are not a live production certificate.

# Changelog

All notable changes to the Financial Document Intelligence System (FDIS) are documented here.

## [Unreleased] - 2026-11-22
### Changed
- Replaced hosted HF embeddings with pinned build-time public MiniLM ONNX assets and local CPU inference. No HF token/runtime hosted inference; Puter remains the separate answer writer.
- Added token-aware splitting, asset/profile checks, bounded local inference and financial table context. Backend 160 tests and frontend 25 tests passed during the rollout.
- Updated current architecture/runbooks and preserved the five requested project notes. Live signed upload and five retrieval checks passed on a public one-page financial statement. Narrow local top-5 number coverage 29/30 is not answer accuracy; actual Puter generation remains gated by user consent/account authorization.
### Removed
- **Groq provider**: `groq_client.py`, GROQ_API_KEY/GROQ_MODEL settings, health check entry, env/render.yaml entries and provider tests.
- **Server-side answer streaming**: `/api/v1/ask/stream` route and the frontend `streamQuestion` helper. Answers come from the user-authorized Puter browser AI flow; backend retrieval, grounded prompt assembly and citation validation are preserved.
### Kept
- OpenRouter fallback client and settings remain configured-off; removal is a separate pending decision.

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
