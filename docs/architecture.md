# Architecture

Current source overview, not a blanket production-readiness claim. Revised 22 November 2026.

- Next.js/React frontend on Vercel, owner-keyed queries and browser navigation.
- FastAPI backend on Vercel Hobby, using inline ingestion on serverless.
- Supabase Auth, private Storage and Postgres/pgvector.
- MiniLM embeddings run locally in the backend using pinned, integrity-checked ONNX weights from the public Hugging Face model repository. No hosted HF inference or HF token.
- Answers are generated server-side on the Groq free plan. Local embeddings do not replace the answer-writing model.

## Upload and search

The browser requests an owner-scoped signed upload URL, uploads directly to the private bucket, then asks the backend to ingest the stored PDF. The current deployment's app acceptance cap is 4 MiB; bucket admission is a separate limit. The server rechecks the stored object's size and atomically claims ingestion. It parses pages/tables, splits content with page metadata, embeds and saves tagged vectors. No fake ready state is used after an error.

The tokenizer has a 256-wordpiece ceiling. Overlong document chunks are split with overlap, not truncated; overlong questions are rejected. New vectors record the exact model/quantization/pooling/tokenization profile. Incompatible returned search matches fail closed. Table continuations repeat the source page context and extracted first rows, but extraction and reading-order recovery remain heuristic, not a verified accounting schema.

The encoder loads one ONNX session per warm process. Each input is encoded independently to avoid dynamic-quantization batch-neighbor effects. One CPU thread and a per-process inference lock bound local concurrency. Parsing and embedding have cooperative budgets; documents also have a chunk cap. These are not a durable job system or a distributed spending/abuse quota. The host can still terminate a request and `/tmp` is not persistent storage.

A Postgres-backed worker path remains for a long-running host, with claims, heartbeats and fenced writes. It is not used on Vercel. The former Render service is preserved as rollback, not silently reactivated.

## Access and deletion

Retrieval restricts ready documents to the authenticated owner before vector search. The 0004 safe-delete migration was applied to the existing hosted project during the earlier authorized hosting change; its deletion path fences worker writes and removes storage before the row/chunks. This is not permission to migrate another database or re-index/reset existing documents. The separate 0005 proposal is not part of this rollout.

There is no open notify endpoint. Browser history is account-scoped localStorage, not a cloud memo database. Statements/Comparison/Insights are explicitly unavailable; there is no fabricated structured-financial dataset.

## Server-side Groq answer path

No login is shown. Each visitor gets a private Supabase anonymous (guest) session; the same bearer-token verification and owner-scoped RLS as named accounts apply, so one guest can never read another guest's or an old account's documents. For each question, the backend retrieves owner-allowed passages, spends one atomic daily quota unit (per guest and one global budget sized under the Groq free plan's daily token cap), then calls the pinned Groq model with the question and those passages. The API key never leaves the server; the original PDF and FDIS tokens are never sent.

The model is server-pinned with no caller override, streaming disabled, output capped, and a completed (`stop`) answer whose citation markers validate against the retrieved passages is required; one regeneration is allowed, then an honest error. Citation markers are not proof of correct amounts, years or semantic support. Quota exhaustion, provider errors and incomplete answers surface as errors, never a paid fallback.

Guest uploads carry a 24-hour `session_expires_at` and are removed (row, chunks, stored PDF) by a traffic-ridden sweep plus a daily cron endpoint. `DELETE /session` deletes a guest's documents, usage rows and auth identity on demand. Named (old Google) accounts have no expiry and are never swept. Anonymous sign-in is scriptable: the global daily answer budget, per-guest quotas, the 5-PDF limit and per-minute rate limits bound, but cannot eliminate, automated abuse; a CAPTCHA on anonymous sign-in remains an option.

## Evidence boundaries

Local unit/fixture tests, a successful deployment, real-PDF retrieval and actual live answer generation are different checks. Release reports must identify which were performed. Public test reports do not establish suitability for confidential financial documents or a commercial uptime guarantee. See `deployment.md` and the backend README for deployment steps and limits.
