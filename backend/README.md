# FDIS Backend Engine

FastAPI, private Supabase storage/pgvector, CPU-only MiniLM embeddings and server-side Groq free-plan answers.

## Run locally

```sh
uv sync --frozen
uv run python scripts/fetch_embedding_model.py
# Copy .env.example to .env and fill Supabase settings, then:
uv run uvicorn src.api.main:app --reload
uv run pytest -q
```

The download script fetches public `sentence-transformers/all-MiniLM-L6-v2` artifacts at one pinned revision and checks byte sizes and SHA-256. No HF token is required. The model is not committed to Git. CI, the Dockerfile and Vercel's build script run the same fetch/verify step. A missing or corrupt model fails closed; the application never downloads a replacement during a request.

Runtime uses the roughly 23 MB ONNX quantized model, a tokenizer, masked mean pooling and L2 normalization to produce 384-dimensional vectors. Each input is run separately because dynamic quantization can otherwise vary activation scales with batch neighbors. One inference runs per process at a time with one CPU thread and a bounded wait/work budget. This is not a distributed quota.

PDF chunks use the real tokenizer's 256-wordpiece ceiling, with overlapping splits instead of silent truncation. Questions above that limit are rejected, not silently shortened. Documents have a 2,000-chunk default work cap and a 45-second cooperative parsing budget. PDF parsing and native table extraction are heuristic. A single native operation cannot be forcibly interrupted by these cooperative checks.

New vectors carry an embedding-profile tag. Returned search matches from a different or missing profile are rejected, not silently mixed. Changing model, quantization, pooling or tokenization may require a separately approved re-index. Never reset existing data as part of a model update.

## Vercel

The backend project uses the FastAPI preset and the entrypoint in `pyproject.toml`. Its build script downloads/verifies the assets; `vercel.json` explicitly includes them and sets a 300-second function maximum. Generated model files are private function assets, not a public/static mount. The frontend continues to call the backend through `NEXT_PUBLIC_API_URL`.

No hosted HF inference, HF token, Cloudflare account or paid embedding API is used. The tokenizer package can bring the HF Hub library transitively; it is not called by the application. Downloading public model weights at build time is different from sending documents to a hosted inference API. The backend still consumes its hosting CPU/memory/network allowance.

Answers come from the Groq free plan (`openai/gpt-oss-120b`), called only from this backend with a server-only key; the model is pinned and there is no paid fallback. Daily free quotas are enforced per guest and globally. Semantic answer correctness still needs independent checks. Local embeddings do not make the answer model unlimited or offline.

Model attribution and Apache 2.0 license: `licenses/`.
