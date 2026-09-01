# Financial Document Intelligence System (FDIS)

> A production-style **Retrieval-Augmented Generation (RAG)** system for querying Peruvian bank annual reports — built end-to-end from document ingestion to a streaming chat UI, with an LLM-as-judge evaluation framework.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-16-black.svg)](https://nextjs.org/)
[![Tests](https://img.shields.io/badge/tests-268%20passing-brightgreen.svg)](#testing)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## What This Project Demonstrates

This project was built **phase by phase** as an AI Engineering portfolio piece. Every component was written from scratch to show understanding of the underlying mechanics — not just gluing frameworks together.

| Area | Implementation |
|---|---|
| **RAG Pipeline** | Full ingest → chunk → embed → retrieve → generate loop |
| **Document Parsing** | PDF (pypdf) and plain-text ingestion with metadata |
| **Chunking Optimization** | Recursive character splitting; chunk size tuned via empirical evaluation |
| **Embeddings** | `all-MiniLM-L6-v2` via `sentence-transformers` (local, no API key) |
| **Vector Search** | FAISS with cosine similarity, retrieval scores, and source filtering |
| **Hybrid Retrieval** | BM25 + FAISS with Reciprocal Rank Fusion (RRF) |
| **LLM Generation** | Groq API (llama / qwen3 models) — pluggable via Abstract Base Class |
| **Streaming API** | FastAPI + Server-Sent Events; per-request model selection |
| **Streaming UI** | Next.js 16 chat interface with token streaming and citation display |
| **LLM-as-Judge Eval** | Custom faithfulness scorer (0–3 scale) with score extraction heuristics |
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
| **qwen3:14b** | **off** | **FAISS** | **94%** | **100%** | **~8s** ★ |
| qwen3:14b | on | FAISS | 94% | 100% | ~22s |
| qwen3:14b | off | FAISS + CrossEncoder | 78% | 100% | ~9s |
| qwen3:14b | off | BM25 + FAISS (RRF) | 86% | 100% | ~9s |

> Faithfulness improved **+30 percentage points** (63.9% → 94%) after two rounds of optimization: chunk size tuning (800/100 tokens) and fixing the judge prompt to read actual chunk content instead of citation filenames.

**Experiment findings:**

- **Extended thinking (think=True)** did not improve faithfulness (94% in both modes) but added **2.7× latency** (~22s vs ~8s). For grounded RAG the bottleneck is retrieval quality, not reasoning depth.

- **Cross-encoder reranking** hurt faithfulness (78% vs 94%). `ms-marco-MiniLM-L-6-v2` was trained on English web search — domain mismatch with Spanish financial documents. A multilingual cross-encoder would likely recover the gap.

- **Hybrid BM25+FAISS (RRF)** also underperformed pure FAISS (86% vs 94%). The dense embeddings already capture keyword overlap effectively for this domain. BM25 introduces noise by surfacing chunks with surface-level term matches that are semantically off-topic.

- **`qwen3:14b`, FAISS only, no extras** is the optimal config at 94% faithfulness and ~8s latency — a reminder that retrieval optimization (chunk size, overlap) often outperforms architectural complexity.

---

## Architecture

```
                        ┌─────────────────────────────────────┐
                        │         Annual Reports (PDF)         │
                        │   Interbank 2025 · Scotiabank 2025   │
                        └──────────────────┬──────────────────┘
                                           │
                              ┌────────────▼────────────┐
                              │   Ingestion & Chunking   │
                              │  RecursiveCharSplitter   │
                              │  chunk_size=800  ovlp=100│
                              └────────────┬────────────┘
                                           │
                              ┌────────────▼────────────┐
                              │       Embeddings         │
                              │  all-MiniLM-L6-v2        │
                              │  384-dim · local         │
                              └────────────┬────────────┘
                                           │
                              ┌────────────▼────────────┐
                              │      FAISS Index         │
                              │  943 chunks · cosine sim │
                              └────────────┬────────────┘
                                           │
          User Question ──────►  ┌─────────▼──────────┐
                                 │    RAG Pipeline      │
                                 │  retrieve top-k      │
                                 │  build context       │
                                 │  generate answer     │
                                 └─────────┬──────────┘
                                           │
                    ┌──────────────────────▼──────────────────────┐
                    │              FastAPI (uvicorn)               │
                    │  POST /ask · POST /ask/stream · GET /models  │
                    └──────────────────────┬──────────────────────┘
                                           │ SSE tokens
                              ┌────────────▼────────────┐
                              │     Next.js 16 Chat UI   │
                              │  Model selector · Filter │
                              │  Citations · Scores      │
                              └─────────────────────────┘
```

### Design Decisions

**Why FAISS over a managed vector DB?**
FAISS keeps the project fully local — no cloud dependencies, no API keys, reproducible on any machine. The `BaseVectorStore` ABC makes it trivially swappable for Pinecone or Qdrant in production.

**Why Groq as the LLM backend?**
Groq provides fast hosted inference with a free tier — no local GPU required. The `BaseGenerator` ABC lets you swap to any other backend with a one-line factory call.

**Why a custom LLM-as-judge instead of RAGAS?**
RAGAS requires an OpenAI key for grading; this project scores faithfulness with the same local models used for generation. The judge parses scores from the *tail* of the response (not the first digit) to avoid false matches on citation numbers like `[2]`.

**Why chunk_size=800?**
Empirically determined via `scripts/chunk_experiment.py`: the 800/100 config reduced chunk count from 1,421 to 943 (fewer, denser chunks) while maintaining retrieval quality, improving faithfulness from 63.9% to 83.3%.

---

## Quick Start — Docker (recommended)

```bash
git clone https://github.com/Fardin7798/financial-document-intelligence-system
cd financial-document-intelligence-system

# Start everything (API + Frontend)
docker compose up
```

- **Chat UI** → http://localhost:3000
- **API docs** → http://localhost:8000/docs

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
# → http://localhost:8000/docs
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
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
├── src/financial_rag/
│   ├── ingestion/           # BaseLoader, TextLoader, PDFLoader, factory
│   ├── chunking/            # RecursiveCharacterSplitter, Chunk dataclass
│   ├── embeddings/          # BaseEmbedder, SentenceTransformerEmbedder, MockEmbedder
│   ├── retrieval/           # VectorRetriever, HybridRetriever (BM25+FAISS+RRF)
│   ├── generation/          # BaseGenerator, OllamaGenerator, ClaudeGenerator, MockGenerator
│   ├── pipeline/            # RAGPipeline, RAGResponse, factory
│   ├── api/                 # FastAPI app, routes, schemas (SSE streaming)
│   ├── evaluation/          # LLM-as-judge, BenchmarkRunner, EvalResult, EvalSummary
│   └── config.py            # pydantic-settings config
├── frontend/                # Next.js 16 chat UI
│   └── src/
│       ├── app/             # Root page layout
│       ├── components/      # Sidebar (model/filter/top-k), ChatInput, MessageBubble
│       ├── hooks/           # useChat (streaming state machine)
│       └── lib/             # API client, TypeScript types
├── scripts/
│   ├── build_index.py       # Build FAISS index with configurable chunk params
│   ├── chunk_experiment.py  # Grid search over chunk sizes
│   └── evaluate.py          # CLI for running benchmark configs
├── tests/
│   ├── unit/                # 216 tests — API, pipeline, chunking, retrieval, eval
│   └── integration/         # 32 end-to-end tests — real components, no Ollama needed
├── docker/
│   ├── Dockerfile.api
│   ├── Dockerfile.frontend
│   └── init-ollama.sh
├── data/
│   ├── samples/             # Interbank 2025 (162pp) · Scotiabank Perú 2025 (120pp)
│   ├── processed/           # FAISS index (943 chunks · 384-dim)
│   └── eval/                # Benchmark results (CSV + JSON)
├── docs/
│   ├── architecture.md
│   └── learning_notes.md
├── docker-compose.yml
├── pyproject.toml
└── Makefile
```

---

## Evaluation Framework

The benchmark runs a 12-question set across three categories against any pipeline configuration:

| Category | Questions | Purpose |
|---|---|---|
| **Factual** (`ib_*`, `sb_*`) | 8 | Test grounded retrieval of specific financial data |
| **Analytical** | 2 | Test multi-chunk synthesis (e.g., risk management) |
| **Out-of-scope** (`oos_*`) | 2 | Test graceful refusal (PBI data, Bitcoin) |

**Faithfulness scoring (LLM-as-judge, 0–3 scale):**

```
3 — Fully grounded: every claim traces to the retrieved chunks
2 — Mostly grounded: minor unsupported additions
1 — Partially grounded: unsupported claims present
0 — Hallucination: contradicts sources or invents information
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

- **216 unit tests** — document ingestion, chunking, embeddings, vector store, retrieval (FAISS + hybrid), generation (Ollama + Claude + Mock), RAG pipeline, FastAPI endpoints, evaluation runner and metrics, CSV/JSON report serialization.
- **32 integration tests** — real components wired together (in-memory FAISS, MockGenerator); covers VectorRetriever pipeline, HybridRetriever pipeline, multi-turn conversation, and all FastAPI endpoints. No external services needed.

The API tests use a **mock pipeline injection pattern** — `app.state.pipeline` is replaced before the TestClient starts, so no Ollama or FAISS index is needed to run the suite.

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
| LLM Backend | Ollama (qwen3:4b / 8b / 14b) · Anthropic Claude API (optional) |
| Sparse Retrieval | rank-bm25 + Reciprocal Rank Fusion |
| API | FastAPI + uvicorn (SSE streaming) |
| Frontend | Next.js 16, TypeScript, Tailwind CSS, shadcn/ui |
| Testing | pytest (268 tests: unit + integration) |
| Containerization | Docker Compose |
| Config | pydantic-settings |

---

## License

MIT

---

---

# Sistema de Inteligencia de Documentos Financieros (FDIS)

> Sistema de **Generación Aumentada por Recuperación (RAG)** de nivel producción para consultar memorias anuales de bancos peruanos — construido de principio a fin, desde la ingesta de documentos hasta una UI de chat con streaming, incluyendo un framework de evaluación con LLM como juez.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-16-black.svg)](https://nextjs.org/)
[![Tests](https://img.shields.io/badge/tests-268%20passing-brightgreen.svg)](#testing)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Qué demuestra este proyecto

Este proyecto fue construido **fase por fase** como pieza de portafolio en Ingeniería de IA. Cada componente fue escrito desde cero para mostrar comprensión de los mecanismos internos — no solo conectar frameworks.

| Área | Implementación |
|---|---|
| **Pipeline RAG** | Ciclo completo: ingestar → chunking → embeber → recuperar → generar |
| **Parseo de documentos** | Ingesta de PDFs (pypdf) y texto plano con metadatos |
| **Optimización de chunks** | División recursiva de caracteres; tamaño calibrado con evaluación empírica |
| **Embeddings** | `all-MiniLM-L6-v2` con `sentence-transformers` (local, sin API key) |
| **Búsqueda vectorial** | FAISS con similitud coseno, scores de recuperación y filtro por fuente |
| **Recuperación híbrida** | BM25 + FAISS con Reciprocal Rank Fusion (RRF) |
| **Generación con LLM** | Ollama (familia qwen3) + Anthropic Claude API — intercambiables mediante Clase Base Abstracta |
| **API con streaming** | FastAPI + Server-Sent Events; selección de modelo por petición |
| **UI con streaming** | Chat en Next.js 16 con streaming de tokens y visualización de citas |
| **Evaluación LLM-juez** | Scorer de fidelidad propio (escala 0–3) con heurísticas de extracción de puntaje |
| **Benchmark runner** | Evaluación multi-configuración: modelos, top-k, think-mode, variantes de recuperación |
| **Experimentos de chunking** | Búsqueda en grilla de tamaños de chunk con reconstrucción automática del índice |
| **Contenedorización** | Docker Compose (API + Frontend + Ollama) para despliegue con un comando |
| **Testing** | 268 tests: unitarios + integración end-to-end; patrón de inyección de pipeline mock |

---

## Resultados principales

Evaluado sobre un benchmark de 12 preguntas: recuperación factual, análisis de riesgo y detección de preguntas fuera de alcance, sobre dos memorias anuales reales.

| Modelo | think | Recuperador | Fidelidad | Source Hit Rate | Generación promedio |
|---|---|---|---|---|---|
| qwen3:4b | off | FAISS | 58% | 100% | ~35s |
| qwen3:8b | off | FAISS | 58% | 100% | ~5s |
| **qwen3:14b** | **off** | **FAISS** | **94%** | **100%** | **~8s** ★ |
| qwen3:14b | on | FAISS | 94% | 100% | ~22s |
| qwen3:14b | off | FAISS + CrossEncoder | 78% | 100% | ~9s |
| qwen3:14b | off | BM25 + FAISS (RRF) | 86% | 100% | ~9s |

> La fidelidad mejoró **+30 puntos porcentuales** (63.9% → 94%) tras dos rondas de optimización: ajuste del tamaño de chunk (800/100 tokens) y corrección del prompt del juez para leer el contenido real de los chunks en vez de solo los nombres de archivo.

**Hallazgos de los experimentos:**

- **Razonamiento extendido (think=True)** no mejoró la fidelidad (94% en ambos modos), pero añadió **2.7× más latencia** (~22s vs ~8s). En RAG con grounding, el cuello de botella es la calidad de la recuperación, no la profundidad del razonamiento.

- **Re-ranking con cross-encoder** redujo la fidelidad (78% vs 94%). El modelo `ms-marco-MiniLM-L-6-v2` fue entrenado en búsqueda web en inglés — desajuste de dominio con documentos financieros en español. Un cross-encoder multilingüe probablemente recuperaría la diferencia.

- **BM25+FAISS híbrido (RRF)** también quedó por debajo del FAISS puro (86% vs 94%). Los embeddings densos ya capturan efectivamente la coincidencia de palabras clave para este dominio. BM25 introduce ruido al traer chunks con coincidencias superficiales que son semánticamente irrelevantes.

- **`qwen3:14b`, solo FAISS, sin extras** es la configuración óptima con 94% de fidelidad y ~8s de latencia — un recordatorio de que la optimización de la recuperación (tamaño de chunk, solapamiento) suele superar la complejidad arquitectónica.

---

## Arquitectura

```
                        ┌─────────────────────────────────────┐
                        │        Memorias Anuales (PDF)        │
                        │   Interbank 2025 · Scotiabank 2025   │
                        └──────────────────┬──────────────────┘
                                           │
                              ┌────────────▼────────────┐
                              │    Ingesta y Chunking    │
                              │  RecursiveCharSplitter   │
                              │  chunk_size=800  ovlp=100│
                              └────────────┬────────────┘
                                           │
                              ┌────────────▼────────────┐
                              │        Embeddings        │
                              │  all-MiniLM-L6-v2        │
                              │  384-dim · local         │
                              └────────────┬────────────┘
                                           │
                              ┌────────────▼────────────┐
                              │      Índice FAISS        │
                              │  943 chunks · cos sim    │
                              └────────────┬────────────┘
                                           │
        Pregunta usuario ──►  ┌────────────▼────────────┐
                              │     Pipeline RAG          │
                              │  recuperar top-k         │
                              │  construir contexto      │
                              │  generar respuesta       │
                              └────────────┬────────────┘
                                           │
                    ┌──────────────────────▼──────────────────────┐
                    │              FastAPI (uvicorn)               │
                    │  POST /ask · POST /ask/stream · GET /models  │
                    └──────────────────────┬──────────────────────┘
                                           │ tokens SSE
                              ┌────────────▼────────────┐
                              │    UI de Chat Next.js 16 │
                              │  Selector modelo · Filtro│
                              │  Citas · Scores          │
                              └─────────────────────────┘
```

### Decisiones de diseño

**¿Por qué FAISS en vez de una base de datos vectorial gestionada?**
FAISS mantiene el proyecto completamente local — sin dependencias en la nube, sin API keys, reproducible en cualquier máquina. La ABC `BaseVectorStore` permite cambiarlo por Pinecone o Qdrant en producción con mínimo esfuerzo.

**¿Por qué Ollama + Claude API como backends duales?**
Ollama provee inferencia local que preserva la privacidad — ningún dato sale de la máquina, ideal para documentos financieros. La ABC `BaseGenerator` permite cambiar al API de Anthropic Claude (con prompt caching) o cualquier otro backend con una sola línea en la factory.

**¿Por qué un LLM-juez propio en vez de RAGAS?**
RAGAS requiere una API key de OpenAI para evaluar; este proyecto puntúa la fidelidad con los mismos modelos locales usados para la generación. El juez extrae el puntaje del *final* de la respuesta (no del primer dígito) para evitar falsos matches en números de citas como `[2]`.

**¿Por qué chunk_size=800?**
Determinado empíricamente con `scripts/chunk_experiment.py`: la configuración 800/100 redujo el total de chunks de 1,421 a 943 (chunks más densos) manteniendo la calidad de recuperación, mejorando la fidelidad de 63.9% a 83.3%.

---

## Inicio rápido — Docker (recomendado)

```bash
git clone https://github.com/Fardin7798/financial-document-intelligence-system
cd financial-document-intelligence-system

# Iniciar todo (API + Frontend + Ollama)
docker compose up

# Descargar el modelo por defecto (solo la primera vez — ~3 GB)
docker compose exec ollama ollama pull qwen3:8b
```

- **UI de Chat** → http://localhost:3000
- **Documentación API** → http://localhost:8000/docs

---

## Configuración local

### Requisitos previos

- Python 3.11+
- [Ollama](https://ollama.com/) instalado y en ejecución
- Node.js 18+ (para el frontend)

### Backend

```bash
# 1. Crear entorno virtual e instalar dependencias
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 2. Copiar configuración del entorno
cp .env.example .env

# 3. Descargar un modelo
ollama pull qwen3:8b

# 4. Construir el índice vectorial a partir de los documentos
python scripts/build_index.py --chunk-size 800 --chunk-overlap 100

# 5. Iniciar la API
uvicorn financial_rag.api.app:app --reload
# → http://localhost:8000/docs
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

### Opcional: backend con Claude API

```bash
pip install -e ".[claude]"
export ANTHROPIC_API_KEY=tu_clave
```

Luego pasa `backend="claude"` a `create_generator()` o usa la factory directamente. El sistema prompt se almacena en caché automáticamente para reducir costo y latencia en llamadas repetidas.

---

## Estructura del proyecto

```
financial-document-intelligence-system/
├── src/financial_rag/
│   ├── ingestion/           # BaseLoader, TextLoader, PDFLoader, factory
│   ├── chunking/            # RecursiveCharacterSplitter, dataclass Chunk
│   ├── embeddings/          # BaseEmbedder, SentenceTransformerEmbedder, MockEmbedder
│   ├── retrieval/           # VectorRetriever, HybridRetriever (BM25+FAISS+RRF)
│   ├── generation/          # BaseGenerator, OllamaGenerator, ClaudeGenerator, MockGenerator
│   ├── pipeline/            # RAGPipeline, RAGResponse, factory
│   ├── api/                 # App FastAPI, rutas, esquemas (streaming SSE)
│   ├── evaluation/          # LLM-juez, BenchmarkRunner, EvalResult, EvalSummary
│   └── config.py            # Configuración con pydantic-settings
├── frontend/                # UI de chat en Next.js 16
│   └── src/
│       ├── app/             # Layout de página raíz
│       ├── components/      # Sidebar (modelo/filtro/top-k), ChatInput, MessageBubble
│       ├── hooks/           # useChat (máquina de estados de streaming)
│       └── lib/             # Cliente API, tipos TypeScript
├── scripts/
│   ├── build_index.py       # Construir índice FAISS con parámetros configurables
│   ├── chunk_experiment.py  # Búsqueda en grilla de tamaños de chunk
│   └── evaluate.py          # CLI para ejecutar configuraciones de benchmark
├── tests/
│   ├── unit/                # 216 tests — API, pipeline, chunking, recuperación, evaluación
│   └── integration/         # 32 tests end-to-end — componentes reales, sin Ollama
├── docker/
│   ├── Dockerfile.api
│   ├── Dockerfile.frontend
│   └── init-ollama.sh
├── data/
│   ├── samples/             # Interbank 2025 (162pp) · Scotiabank Perú 2025 (120pp)
│   ├── processed/           # Índice FAISS (943 chunks · 384-dim)
│   └── eval/                # Resultados del benchmark (CSV + JSON)
├── docs/
│   ├── architecture.md
│   └── learning_notes.md
├── docker-compose.yml
├── pyproject.toml
└── Makefile
```

---

## Framework de evaluación

El benchmark ejecuta 12 preguntas en tres categorías contra cualquier configuración de pipeline:

| Categoría | Preguntas | Propósito |
|---|---|---|
| **Factual** (`ib_*`, `sb_*`) | 8 | Recuperación grounded de datos financieros específicos |
| **Analítica** | 2 | Síntesis multi-chunk (ej. gestión de riesgos) |
| **Fuera de alcance** (`oos_*`) | 2 | Rechazo correcto (datos del PBI, Bitcoin) |

**Puntaje de fidelidad (LLM-juez, escala 0–3):**

```
3 — Totalmente grounded: cada afirmación se remite a los chunks recuperados
2 — Mayormente grounded: adiciones menores sin respaldo
1 — Parcialmente grounded: afirmaciones sin respaldo presentes
0 — Alucinación: contradice fuentes o inventa información
```

**Ejecutar el benchmark:**

```bash
# Comparar 3 modelos con top_k=5
python scripts/evaluate.py --models qwen3:4b qwen3:8b qwen3:14b --top-k 5 --out data/eval/final

# Experimento think=True vs think=False (qwen3:8b y qwen3:14b en paralelo)
python scripts/evaluate.py --think-experiment --out data/eval/final

# Solo con razonamiento extendido
python scripts/evaluate.py --models qwen3:14b --top-k 5 --think --out data/eval/final
```

Los resultados se guardan como CSV (detalle por pregunta, incluyendo el flag `think`) y JSON (resumen por configuración), fusionándose con ejecuciones previas de forma no destructiva.

---

## Testing

```bash
# Solo tests unitarios
pytest tests/unit/ -v

# Tests de integración (sin Ollama ni índice FAISS)
pytest tests/integration/ -v

# Suite completa
pytest tests/ -v

# Con cobertura
pytest tests/ --cov=financial_rag --cov-report=term-missing
```

**268 tests** en dos suites:

- **216 tests unitarios** — ingesta, chunking, embeddings, vector store, recuperación (FAISS + híbrida), generación (Ollama + Claude + Mock), pipeline RAG, endpoints FastAPI, runner de evaluación y métricas, serialización CSV/JSON.
- **32 tests de integración** — componentes reales conectados (FAISS en memoria, MockGenerator); cubre pipeline con VectorRetriever, pipeline con HybridRetriever, conversación multi-turno y todos los endpoints FastAPI. No se requieren servicios externos.

Los tests de API usan un **patrón de inyección de pipeline mock** — `app.state.pipeline` se reemplaza antes de iniciar el TestClient, por lo que no se necesita Ollama ni índice FAISS para correr la suite.

---

## Comandos de desarrollo

```bash
make help          # Lista todos los targets
make test          # Ejecutar pytest
make lint          # ruff + mypy
make format        # ruff format
make api           # Iniciar servidor FastAPI
make evaluate      # Ejecutar benchmark completo
```

---

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| Lenguaje | Python 3.11+ |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) |
| Vector Store | FAISS (faiss-cpu) |
| Backend LLM | Ollama (qwen3:4b / 8b / 14b) · Anthropic Claude API (opcional) |
| Recuperación sparse | rank-bm25 + Reciprocal Rank Fusion |
| API | FastAPI + uvicorn (streaming SSE) |
| Frontend | Next.js 16, TypeScript, Tailwind CSS, shadcn/ui |
| Testing | pytest (268 tests: unitarios + integración) |
| Contenedorización | Docker Compose |
| Configuración | pydantic-settings |

---

## Licencia

MIT
