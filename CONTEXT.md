# CONTEXT.md — Living Workspace Memory & Active State Tracker

## Current Milestone & Status
- **System**: Financial Document Intelligence System (FDIS)
- **Status**: Production Full-Stack Deployed to Vercel (Serverless Python Backend + Next.js Frontend)
- **Git Commit**: `39cb206` pushed to `origin/main` on GitHub
- **Hosting**: 100% Free Tier, Zero-Card Serverless on Vercel Cloud
- **Local Machine**: Zero laptop load (0% CPU/RAM consumption).

## Production Live URLs (Vercel Serverless)
- **Primary Domain**: [https://financial-doc-ai.vercel.app](https://financial-doc-ai.vercel.app)
- **Alias Domain**: [https://fdis-intelligence.vercel.app](https://fdis-intelligence.vercel.app)
- **Live Health Endpoint**: [https://financial-doc-ai.vercel.app/api/v1/health](https://financial-doc-ai.vercel.app/api/v1/health) (Status: `healthy`, DB: `connected`)
- **Live Documents Endpoint**: [https://financial-doc-ai.vercel.app/api/v1/documents](https://financial-doc-ai.vercel.app/api/v1/documents) (Total: 2 documents indexed)
- **Live RAG Context Endpoint**: `POST https://financial-doc-ai.vercel.app/api/v1/ask/context` (Hugging Face Inference API embeddings + Supabase pgvector)
- **Live SSE Streaming Endpoint**: `POST https://financial-doc-ai.vercel.app/api/v1/ask/stream` (Groq LPU grounded SSE token streaming)

## Major Architectural Transformation (Phase: Lightweight Vercel Serverless)
1. **Eliminated Heavy Local PyTorch (~850MB -> ~40MB)**:
   - Replaced `sentence-transformers` with lightweight `huggingface-hub>=0.28.0` + `numpy`.
   - Utilizes Hugging Face Inference API (`sentence-transformers/all-MiniLM-L6-v2`) via verified serverless token `HF_TOKEN`.
   - Generates exact 384-dimensional vector embeddings with ~0.8s latency without downloading 400MB torch weights.
2. **Vercel Native Serverless Integration**:
   - `frontend/api/index.py` exposes the FastAPI application directly to Vercel's Python runtime.
   - `frontend/next.config.mjs` and `frontend/vercel.json` rewrite `/api/v1/*` directly to `api/index.py`, eliminating CORS and running full-stack under a single domain.
   - Dual-mounted routes in `main.py` ensure both `/api/v1/...` and `/...` are seamlessly resolved.
3. **Verified Live Endpoints**:
   - `/api/v1/health`: Confirmed DB connection, Groq, OpenRouter, and Resend availability.
   - `/api/v1/documents`: Confirmed document list and chunk counts.
   - `/api/v1/ask/context`: Confirmed vector search with Hugging Face API and prompt generation.
   - `/api/v1/ask/stream`: Confirmed token-by-token SSE streaming from Groq LPU.
4. **Codebase Synchronized**:
   - All commits pushed to GitHub repository: `https://github.com/ashhal-kaleem/financial-document-intelligence-system`.
