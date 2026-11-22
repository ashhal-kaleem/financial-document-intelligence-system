# Product requirements: Financial Document Intelligence System

Reconciled 22 November 2026. The product remains financial-document RAG, not a generic chatbot or a new analytics product. Current evidence and open verification gates live in `production-readiness.md`.

## User outcome

A signed-in user can upload their financial PDF, wait until indexing is explicitly ready, select the report and ask a question. The answer should identify its supporting source pages and admit insufficient context. The user must be able to open the cited PDF and check amounts, units and periods.

## Current implemented behavior

- Next.js workspace, Supabase authentication and a private per-owner document library.
- Browser-to-private-storage signed uploads, backend file validation and inline ingestion on Vercel. Queued processing is a non-Vercel compatibility path, not an active durable Vercel worker.
- Text/table PDF extraction, page-aware/token-bounded chunks, local pinned MiniLM embeddings and owned pgvector retrieval. Missing/incompatible vector profiles fail rather than mixing silently.
- A server-side answer API on the Groq free plan. The model is pinned server-side with no caller choice, daily free quotas are enforced per guest and globally, and no paid fallback exists.
- Browser-local conversations, citation source viewer and safe owner-only document deletion. No cloud chat archive or export.

Groq (free plan) is the final-answer writer, called only from the backend. It is not an embeddings API. HF provides pinned public build-time model artifacts, not a runtime inference service. Cloudflare is not in the chosen runtime.

## Acceptance boundaries

- Ready means real extraction/indexing completed, not that upload was merely accepted. Processing/error/deleting states must not present as ready.
- Non-owners must not read, retrieve or delete another user's reports. PDF responses stay private/no-store.
- No financial answer should be treated as correct solely because retrieval returned a number or citation IDs validated. Source amount, scale, year, quarter and arithmetic must match; absent evidence should lead to abstention.
- Only text-based PDFs within the current 4 MiB app cap are accepted. Scanned, empty and encrypted PDFs fail clearly. Default page/chunk/parser-work limits also apply.
- Document text goes to local backend embeddings. The Groq API receives only the question and retrieved excerpts/metadata when an answer is requested; the key and PDF stay server-side. The free plan's daily quotas apply; they do not establish unlimited use.
- Existing user data, re-indexing, schema changes, paid resources and new processor disclosures need their own approval.

## Still outside the verified product

Broadly measured financial-answer accuracy, reliable Hinglish coverage, OCR, durable background jobs on Vercel, cloud chat/export, financial dashboards, arbitrary larger documents, CAPTCHA/bot resistance on guest sign-in and commercial uptime guarantees.

No launch target overrides these boundaries. Use the dated test/readiness notes to distinguish local tests, successful deployment, live retrieval and real final-answer evidence.
