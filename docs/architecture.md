# Architecture

Current source overview, not an approval or live deployment certificate.

Frontend Next.js/React manages UI state with Zustand and owner-keyed document queries with TanStack Query. Backend FastAPI validates authenticated requests. Services orchestrate ingestion, retrieval and inference. Domain models/chunking/citation formatting sit below services. Supabase, embedding and model clients are adapters. Pin versions from lockfiles, not this prose.

Uploads store a nonclaimable document row and private PDF before queueing. A long-running API worker claims from Postgres, heartbeats and uses attempt-fenced writes. Parsing/embedding run off the asyncio event loop. Vercel's mirrored API is inline-only, not a durable worker host.

Retrieval restricts visible ready documents before embedding/search. Current embeddings call HF feature_extraction with all-MiniLM-L6-v2 and384 dimensions, not local CPU inference. Inference currently uses configured Groq with optional opt-in OpenRouter fallback. User-requested Puter research is not a provider switch. No fallback joins a partial primary stream.

Document passages/metadata are untrusted input. Prompt rules preserve units/year/basis, and completed answers must cite retrieved marker IDs. These controls do not prove semantic grounding or injection resistance. Model stream failure is not success. PDF table extraction is heuristic.

Deletion proposal0004 marks the owned document deleting under lock, fences worker writes, removes the Storage object, then database row/chunks. The migration is not applied hosted. Busy uploads/processing return conflict. Storage failure preserves a retry handle.

No open notify endpoint. Frontend analytics/financial charts remain labeled illustrative samples, not extracted accounting statements. Browser history is account-scoped localStorage, not a cloud memo database. See readiness/deployment docs for unresolved live, privacy, quota and release gates.
