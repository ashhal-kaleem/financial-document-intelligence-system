# Resume and launch wording gate

Updated 22 November 2026. Keep product claims aligned with measured evidence; this file does not authorize publishing outreach or changing the product idea.

## Accurate project description

Built a private financial-document RAG app using Next.js, FastAPI, Supabase/pgvector and local ONNX MiniLM embeddings, with owner-scoped document retrieval, page citations and an opt-in Puter answer flow.

That describes the implementation, not independently measured answer accuracy. The current deployment and tests are documented in production-readiness.md. Public weights are downloaded from HF at build time; hosted HF inference is not used. Puter remains a separate account-based service with its own limits.

## Claims that need more evidence

Do not claim production certification, audit readiness, zero hallucinations, unlimited free usage, sub-second end-to-end performance or business uptime guarantees. Narrow expected-number retrieval on one public PDF page is not answer accuracy. A citation marker is not proof of semantic support.

Before adding performance/quality figures to a resume or launch page, record the independently reviewed dataset, language mix, exact model/profile, source-page recall, numeric/period/currency support, abstention behavior, p50/p95, failure rate, test date and cost/limits. Identify any untested generation or provider boundary.

Screenshots must show the real application state. Never replace failed ingestion, missing provider access or unavailable analytics with demo success.
