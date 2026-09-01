# Architecture

## System Overview

The Financial RAG Assistant is a **Retrieval-Augmented Generation (RAG)** system.
RAG solves a fundamental LLM limitation: models have a fixed knowledge cutoff
and cannot reason over private documents. By retrieving relevant document chunks
at query time and feeding them as context, we enable grounded, citation-backed answers.

## Data Flows

### 1. Ingestion Flow (offline, run once per document set)

```
Raw Documents (PDF / TXT)
        │
        ▼
   [Ingestion Layer]
   - Load file bytes
   - Extract text + metadata (filename, page number, date)
        │
        ▼
   [Chunking Layer]
   - Split text into overlapping chunks
   - Preserve metadata per chunk
        │
        ▼
   [Embedding Layer]
   - sentence-transformers → dense vectors (384-dim)
        │
        ▼
   [Vector Store]
   - FAISS index (L2 / cosine)
   - Metadata stored alongside vectors
```

### 2. Query Flow (online, per user request)

```
User Question (string)
        │
        ▼
   [Embed Question]
   - Same model as ingestion
        │
        ▼
   [Vector Search]
   - Top-K nearest chunks + similarity scores
        │
        ▼
   [Context Assembly]
   - Format chunks with source citations
        │
        ▼
   [LLM Generation]
   - Prompt = system + context + question
   - Backend: Groq | Mock
        │
        ▼
   Answer + Citations + Retrieval Scores
```

### 3. Evaluation Flow (offline, for quality measurement)

```
Test Dataset (question, ground_truth)
        │
        ▼
   [Run Pipeline on Each Question]
        │
        ▼
   [Compute Metrics]
   - Context Recall
   - Answer Faithfulness
   - Answer Relevancy
        │
        ▼
   Evaluation Report (JSON + HTML)
```

## Component Responsibilities

| Component | Module | Responsibility |
|---|---|---|
| Ingestion | `financial_rag.ingestion` | Load and parse documents |
| Chunking | `financial_rag.chunking` | Split text into retrievable units |
| Embeddings | `financial_rag.embeddings` | Dense vector representations |
| Retrieval | `financial_rag.retrieval` | Vector similarity search |
| Generation | `financial_rag.generation` | LLM prompting and response |
| API | `financial_rag.api` | FastAPI HTTP interface |
| UI | `financial_rag.ui` | Streamlit chat interface |
| Evaluation | `financial_rag.evaluation` | Metrics and quality reporting |

## Key Design Decisions

### Why sentence-transformers instead of OpenAI embeddings?
Local-first. No API cost, no rate limits, reproducible. `all-MiniLM-L6-v2` is
a solid 384-dim model that fits in ~80MB RAM and runs fast on CPU.

### Why FAISS instead of a cloud vector DB (Pinecone, Weaviate)?
For a portfolio project, local tools demonstrate the core concepts without
infrastructure dependencies. FAISS is the industry-standard library used
inside Pinecone and others. It's a better learning tool than a managed service.

### Why a pluggable LLM backend?
Different environments have different constraints:
- **Development / CI**: Mock backend (no GPU, no API key needed)
- **Production**: Groq (fast hosted inference, free tier available)

The `BaseLLM` abstraction makes this transparent to the rest of the system.

### Why FastAPI + Streamlit separately?
They serve different users:
- FastAPI: engineers, downstream apps, evaluation scripts
- Streamlit: business stakeholders, demos, quick prototyping

Keeping them separate means the API can evolve independently.

## Scalability Path

This architecture intentionally starts simple. To scale:

1. **Embeddings**: Replace sentence-transformers with a hosted embedding API
2. **Vector Store**: Swap FAISS for Pinecone / Weaviate / pgvector
3. **LLM**: Move from Groq free tier to a hosted model with load balancing
4. **API**: Add authentication, rate limiting, request queuing
5. **Ingestion**: Add async document processing with Celery or a job queue
