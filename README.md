# Financial Document Intelligence System (FDIS)

> A production-style **Retrieval-Augmented Generation (RAG)** system for querying Peruvian bank annual reports â€” built end-to-end from document ingestion to a streaming chat UI, with an LLM-as-judge evaluation framework.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-16-black.svg)](https://nextjs.org/)
[![Tests](https://img.shields.io/badge/tests-268%20passing-brightgreen.svg)](#testing)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## What This Project Demonstrates

This project was built **phase by phase** as an AI Engineering portfolio piece. Every component was written from scratch to show understanding of the underlying mechanics â€” not just gluing frameworks together.

| Area | Implementation |
|---|---|
| **RAG Pipeline** | Full ingest â†’ chunk â†’ embed â†’ retrieve â†’ generate loop |
| **Document Parsing** | PDF (pypdf) and plain-text ingestion with metadata |
| **Chunking Optimization** | Recursive character splitting; chunk size tuned via empirical evaluation |
| **Embeddings** | `all-MiniLM-L6-v2` via `sentence-transformers` (local, no API key) |
| **Vector Search** | FAISS with cosine similarity, retrieval scores, and source filtering |
| **Hybrid Retrieval** | BM25 + FAISS with Reciprocal Rank Fusion (RRF) |
| **LLM Generation** | Groq API (llama / qwen3 models) â€” pluggable via Abstract Base Class |
| **Streaming API** | FastAPI + Server-Sent Events; per-request model selection |
| **Streaming UI** | Next.js 16 chat interface with token streaming and citation display |
| **LLM-as-Judge Eval** | Custom faithfulness scorer (0â€“3 scale) with score extraction heuristics |
| **Benchmark Runner** | Multi-config evaluation: models, top-k, think-mode, retriever variants |
| **Chunking Experiments** | Automated grid search over chunk sizes with index rebuild |
| **Containerization** | Docker Compose (API + Frontend) for one-command deploy |
| **Testing** | 268 tests: unit + end-to-end integration; mock pipeline injection pattern |

---

## Key Results

Evaluated on a 12-question benchmark covering factual retrieval, risk analysis, and out-of-scope detection across two real bank annual reports.

| Model | think | Retriever | Faithfulness | Source Hit Rate | Avg. Generation |
|---|---|---|---|---|---|
| qwen3:4b | off | FAISS | 58% | 100% | ~35s |
| qwen3:8b | off | FAISS | 58% | 100% | ~5s |
| **qwen3:14b** | **off** | **FAISS** | **94%** | **100%** | **~8s** â˜… |
| qwen3:14b | on | FAISS | 94% | 100% | ~22s |
| qwen3:14b | off | FAISS + CrossEncoder | 78% | 100% | ~9s |
| qwen3:14b | off | BM25 + FAISS (RRF) | 86% | 100% | ~9s |

> Faithfulness improved **+30 percentage points** (63.9% â†’ 94%) after two rounds of optimization: chunk size tuning (800/100 tokens) and fixing the judge prompt to read actual chunk content instead of citation filenames.

**Experiment findings:**

- **Extended thinking (think=True)** did not improve faithfulness (94% in both modes) but added **2.7Ã— latency** (~22s vs ~8s). For grounded RAG the bottleneck is retrieval quality, not reasoning depth.

- **Cross-encoder reranking** hurt faithfulness (78% vs 94%). `ms-marco-MiniLM-L-6-v2` was trained on English web search â€” domain mismatch with Spanish financial documents. A multilingual cross-encoder would likely recover the gap.

- **Hybrid BM25+FAISS (RRF)** also underperformed pure FAISS (86% vs 94%). The dense embeddings already capture keyword overlap effectively for this domain. BM25 introduces noise by surfacing chunks with surface-level term matches that are semantically off-topic.

- **`qwen3:14b`, FAISS only, no extras** is the optimal config at 94% faithfulness and ~8s latency â€” a reminder that retrieval optimization (chunk size, overlap) often outperforms architectural complexity.

---

## Architecture

```
                        â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                        â”‚         Annual Reports (PDF)         â”‚
                        â”‚   Interbank 2025 Â· Scotiabank 2025   â”‚
                        â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                                           â”‚
                              â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                              â”‚   Ingestion & Chunking   â”‚
                              â”‚  RecursiveCharSplitter   â”‚
                              â”‚  chunk_size=800  ovlp=100â”‚
                              â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                                           â”‚
                              â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                              â”‚       Embeddings         â”‚
                              â”‚  all-MiniLM-L6-v2        â”‚
                              â”‚  384-dim Â· local         â”‚
                              â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                                           â”‚
                              â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                              â”‚      FAISS Index         â”‚
                              â”‚  943 chunks Â· cosine sim â”‚
                              â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                                           â”‚
          User Question â”€â”€â”€â”€â”€â”€â–º  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                                 â”‚    RAG Pipeline      â”‚
                                 â”‚  retrieve top-k      â”‚
                                 â”‚  build context       â”‚
                                 â”‚  generate answer     â”‚
                                 â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                                           â”‚
                    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                    â”‚              FastAPI (uvicorn)               â”‚
                    â”‚  POST /ask Â· POST /ask/stream Â· GET /models  â”‚
                    â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                                           â”‚ SSE tokens
                              â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                              â”‚     Next.js 16 Chat UI   â”‚
                              â”‚  Model selector Â· Filter â”‚
                              â”‚  Citations Â· Scores      â”‚
                              â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

### Design Decisions

**Why FAISS over a managed vector DB?**
FAISS keeps the project fully local â€” no cloud dependencies, no API keys, reproducible on any machine. The `BaseVectorStore` ABC makes it trivially swappable for Pinecone or Qdrant in production.

**Why Groq as the LLM backend?**
Groq provides fast hosted inference with a free tier â€” no local GPU required. The `BaseGenerator` ABC lets you swap to any other backend with a one-line factory call.

**Why a custom LLM-as-judge instead of RAGAS?**
RAGAS requires an OpenAI key for grading; this project scores faithfulness with the same local models used for generation. The judge parses scores from the *tail* of the response (not the first digit) to avoid false matches on citation numbers like `[2]`.

**Why chunk_size=800?**
Empirically determined via `scripts/chunk_experiment.py`: the 800/100 config reduced chunk count from 1,421 to 943 (fewer, denser chunks) while maintaining retrieval quality, improving faithfulness from 63.9% to 83.3%.

---

## Quick Start â€” Docker (recommended)

```bash
git clone https://github.com/Fardin7798/financial-document-intelligence-system
cd financial-document-intelligence-system

# Start everything (API + Frontend)
docker compose up
```

- **Chat UI** â†’ http://localhost:3000
- **API docs** â†’ http://localhost:8000/docs

---

## Local Development Setup

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.com/) installed and running
- Node.js 18+ (for the frontend)

### Backend

```bash
# 1. Create virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 2. Copy environment config
cp .env.example .env

# 3. Pull a model
ollama pull qwen3:8b

# 4. Build the vector index from sample documents
python scripts/build_index.py --chunk-size 800 --chunk-overlap 100

# 5. Start the API
uvicorn financial_rag.api.app:app --reload
# â†’ http://localhost:8000/docs
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# â†’ http://localhost:3000
```

### Optional: Claude API backend

```bash
pip install -e ".[claude]"
export ANTHROPIC_API_KEY=your_key
```

Then pass `backend="claude"` to `create_generator()` or use the factory directly.

---

## Project Structure

```
financial-document-intelligence-system/
â”œâ”€â”€ src/financial_rag/
â”‚   â”œâ”€â”€ ingestion/           # BaseLoader, TextLoader, PDFLoader, factory
â”‚   â”œâ”€â”€ chunking/            # RecursiveCharacterSplitter, Chunk dataclass
â”‚   â”œâ”€â”€ embeddings/          # BaseEmbedder, SentenceTransformerEmbedder, MockEmbedder
â”‚   â”œâ”€â”€ retrieval/           # VectorRetriever, HybridRetriever (BM25+FAISS+RRF)
â”‚   â”œâ”€â”€ generation/          # BaseGenerator, OllamaGenerator, ClaudeGenerator, MockGenerator
â”‚   â”œâ”€â”€ pipeline/            # RAGPipeline, RAGResponse, factory
â”‚   â”œâ”€â”€ api/                 # FastAPI app, routes, schemas (SSE streaming)
â”‚   â”œâ”€â”€ evaluation/          # LLM-as-judge, BenchmarkRunner, EvalResult, EvalSummary
â”‚   â””â”€â”€ config.py            # pydantic-settings config
â”œâ”€â”€ frontend/                # Next.js 16 chat UI
â”‚   â””â”€â”€ src/
â”‚       â”œâ”€â”€ app/             # Root page layout
â”‚       â”œâ”€â”€ components/      # Sidebar (model/filter/top-k), ChatInput, MessageBubble
â”‚       â”œâ”€â”€ hooks/           # useChat (streaming state machine)
â”‚       â””â”€â”€ lib/             # API client, TypeScript types
â”œâ”€â”€ scripts/
â”‚   â”œâ”€â”€ build_index.py       # Build FAISS index with configurable chunk params
â”‚   â”œâ”€â”€ chunk_experiment.py  # Grid search over chunk sizes
â”‚   â””â”€â”€ evaluate.py          # CLI for running benchmark configs
â”œâ”€â”€ tests/
â”‚   â”œâ”€â”€ unit/                # 216 tests â€” API, pipeline, chunking, retrieval, eval
â”‚   â””â”€â”€ integration/         # 32 end-to-end tests â€” real components, no Ollama needed
â”œâ”€â”€ docker/
â”‚   â”œâ”€â”€ Dockerfile.api
â”‚   â”œâ”€â”€ Dockerfile.frontend
â”‚   â””â”€â”€ init-ollama.sh
â”œâ”€â”€ data/
â”‚   â”œâ”€â”€ samples/             # Interbank 2025 (162pp) Â· Scotiabank PerÃº 2025 (120pp)
â”‚   â”œâ”€â”€ processed/           # FAISS index (943 chunks Â· 384-dim)
â”‚   â””â”€â”€ eval/                # Benchmark results (CSV + JSON)
â”œâ”€â”€ docs/
â”‚   â”œâ”€â”€ architecture.md
â”‚   â””â”€â”€ learning_notes.md
â”œâ”€â”€ docker-compose.yml
â”œâ”€â”€ pyproject.toml
â””â”€â”€ Makefile
```

---

## Evaluation Framework

The benchmark runs a 12-question set across three categories against any pipeline configuration:

| Category | Questions | Purpose |
|---|---|---|
| **Factual** (`ib_*`, `sb_*`) | 8 | Test grounded retrieval of specific financial data |
| **Analytical** | 2 | Test multi-chunk synthesis (e.g., risk management) |
| **Out-of-scope** (`oos_*`) | 2 | Test graceful refusal (PBI data, Bitcoin) |

**Faithfulness scoring (LLM-as-judge, 0â€“3 scale):**

```
3 â€” Fully grounded: every claim traces to the retrieved chunks
2 â€” Mostly grounded: minor unsupported additions
1 â€” Partially grounded: unsupported claims present
0 â€” Hallucination: contradicts sources or invents information
```

**Run the benchmark:**

```bash
# Compare 3 models at top_k=5
python scripts/evaluate.py --models qwen3:4b qwen3:8b qwen3:14b --top-k 5 --out data/eval/final

# think=True vs think=False side-by-side (qwen3:8b and qwen3:14b)
python scripts/evaluate.py --think-experiment --out data/eval/final

# Run with extended thinking mode on a single model
python scripts/evaluate.py --models qwen3:14b --top-k 5 --think --out data/eval/final
```

Results are saved as both CSV (per-question detail, including `think` flag) and JSON (config-level summary), merging with previous runs non-destructively.

## RAG Evaluation (New Framework)

A new lightweight but rigorous evaluation framework has been added to measure retrieval and generation quality against a curated dataset (`scripts/evaluation_dataset.json`).

### Metrics Tracked:
- **Retrieval Quality**: Recall@1, Recall@3, Recall@5, Recall@10, and Mean Reciprocal Rank (MRR).
- **Answer Quality**: Context Recall (are expected facts in context?), Correctness (are expected facts in answer?), and Groundedness (does the LLM judge confirm the answer is fully supported by context without hallucinations?).
- **Document Scoping**: Ensures queries respect document-level filtering (`document_ids`).

### Running the Evaluation
To evaluate retrieval:
```bash
python scripts/evaluate_retrieval.py
```
To evaluate answers:
```bash
python scripts/evaluate_answers.py
```
To run the full suite:
```bash
python scripts/run_evaluation.py
```
Results are saved to the `reports/` directory.

---

## Testing

```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests (no Ollama or FAISS index required)
pytest tests/integration/ -v

# Full suite
pytest tests/ -v

# With coverage
pytest tests/ --cov=financial_rag --cov-report=term-missing
```

**268 tests** across two suites:

- **216 unit tests** â€” document ingestion, chunking, embeddings, vector store, retrieval (FAISS + hybrid), generation (Ollama + Claude + Mock), RAG pipeline, FastAPI endpoints, evaluation runner and metrics, CSV/JSON report serialization.
- **32 integration tests** â€” real components wired together (in-memory FAISS, MockGenerator); covers VectorRetriever pipeline, HybridRetriever pipeline, multi-turn conversation, and all FastAPI endpoints. No external services needed.

The API tests use a **mock pipeline injection pattern** â€” `app.state.pipeline` is replaced before the TestClient starts, so no Ollama or FAISS index is needed to run the suite.

---

## Development Commands

```bash
make help          # List all targets
make test          # Run pytest
make lint          # ruff + mypy
make format        # ruff format
make api           # Start FastAPI server
make evaluate      # Run full benchmark
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) |
| Vector Store | FAISS (faiss-cpu) |
| LLM Backend | Ollama (qwen3:4b / 8b / 14b) Â· Anthropic Claude API (optional) |
| Sparse Retrieval | rank-bm25 + Reciprocal Rank Fusion |
| API | FastAPI + uvicorn (SSE streaming) |
| Frontend | Next.js 16, TypeScript, Tailwind CSS, shadcn/ui |
| Testing | pytest (268 tests: unit + integration) |
| Containerization | Docker Compose |
| Config | pydantic-settings |

---

## License

MIT
