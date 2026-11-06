# Architecture

Current source overview, not an approval or live deployment certificate.

Frontend Next.js/React manages UI state with Zustand and owner-keyed document queries with TanStack Query. Backend FastAPI validates authenticated requests. Services orchestrate ingestion, retrieval and inference. Domain models/chunking/citation formatting sit below services. Supabase, embedding and model clients are adapters. Pin versions from lockfiles, not this prose.

Uploads store a nonclaimable document row and private PDF before queueing. A long-running API worker claims from Postgres, heartbeats and uses attempt-fenced writes. Parsing/embedding run off the asyncio event loop. Vercel's mirrored API is inline-only, not a durable worker host.

Retrieval restricts visible ready documents before embedding/search. Current embeddings call HF feature_extraction with all-MiniLM-L6-v2 and384 dimensions, not local CPU inference. Inference currently uses configured Groq with optional opt-in OpenRouter fallback. User-requested Puter research is not a provider switch. No fallback joins a partial primary stream.

Document passages/metadata are untrusted input. Prompt rules preserve units/year/basis, and completed answers must cite retrieved marker IDs. These controls do not prove semantic grounding or injection resistance. Model stream failure is not success. PDF table extraction is heuristic.

Deletion proposal0004 marks the owned document deleting under lock, fences worker writes, removes the Storage object, then database row/chunks. The migration is not applied hosted. Busy uploads/processing return conflict. Storage failure preserves a retry handle.

No open notify endpoint. Frontend analytics/financial charts remain labeled illustrative samples, not extracted accounting statements. Browser history is account-scoped localStorage, not a cloud memo database. See readiness/deployment docs for unresolved live, privacy, quota and release gates.

## Opt-in Puter path

The chat UI now offers a separate Connect AI step, loads Puter.js only after disclosure/checkbox/model selection, then uses its genuine account popup. Supabase login still gates all document data. Before each question the backend retrieves owner-scoped ready passages, verifies the exact provider-qualified :free model has zero catalog rates and signs a 10-minute owner/citation receipt. The browser sends retrieved passages/question/filenames/page metadata to Puter, not the original PDF or FDIS auth token. It pins provider/model, disables provider fallback, requests a normalized non-streamed capped answer and requires stop plus reported zero model cost. Only after backend marker/receipt checks and a fresh source-visibility check does the UI display the answer. No-context answers make no model call.

Non-streamed completion is deliberate: no stable terminal finish marker was established for every Puter streaming provider. The UI waits rather than treating an iterator EOF as trustworthy completion. Browser answer submissions are untrusted; receipts bind IDs/owner/expiry, not provider provenance or semantic truth. No server-side AI record/commit is created. Real Puter generation was not performed; integration is code/fake-tested only. Catalog preflight cannot atomically lock a third party's price, and reported runtime charges can only be detected after a call. Users must review Puter usage and provider privacy before confidential content. Cancellation may stop local waiting while the upstream model finishes.
