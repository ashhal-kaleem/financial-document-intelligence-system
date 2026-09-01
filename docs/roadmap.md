# Project Roadmap

## Phase Status

| # | Phase | Status | Key Skills |
|---|---|---|---|
| 0 | Project Setup | ✅ Done | `pyproject.toml`, Makefile, project structure |
| 1 | Document Ingestion | ⏳ Next | PDF parsing, metadata, `pypdf` |
| 2 | Chunking | ⬜ | Recursive splitting, overlap, token counting |
| 3 | Embeddings + Vector DB | ⬜ | `sentence-transformers`, FAISS, cosine similarity |
| 4 | Retrieval Baseline | ⬜ | Top-K search, similarity scores, filtering |
| 5 | Grounded Generation | ⬜ | Prompt engineering, citations, LLM abstraction |
| 6 | FastAPI | ⬜ | Async endpoints, Pydantic schemas, OpenAPI docs |
| 7 | Streamlit UI | ⬜ | Chat interface, document upload, score display |
| 8 | Evaluation Pipeline | ⬜ | RAGAS metrics, faithfulness, relevancy |
| 9 | Tests + Code Quality | ⬜ | pytest, ruff, mypy, pre-commit |
| 10 | Docker | ⬜ | Dockerfile, Docker Compose, multi-stage build |
| 11 | GitHub Docs | ⬜ | README polish, diagrams, badges, CONTRIBUTING |
| 12 | Extensions | ⬜ | Hybrid search, re-ranking, streaming, auth |

## Milestones

### MVP (Phases 0–5)
A working CLI pipeline: ingest a PDF, ask a question, get a grounded answer with citations.

### Demo-ready (Phases 0–7)
FastAPI + Streamlit running locally. Can be demoed to a recruiter or technical interviewer.

### Production-style (Phases 0–11)
Tests, Docker, evaluation metrics, clean docs. Ready to be featured on GitHub profile.

### Advanced (Phase 12)
Hybrid search (BM25 + dense), cross-encoder re-ranking, streaming responses, JWT auth.
