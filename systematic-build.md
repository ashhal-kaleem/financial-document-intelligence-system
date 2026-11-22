# Build and release evidence checklist

Updated 22 November 2026. This is the current checklist, not the old Groq/SSE build log. Product purpose is unchanged financial-document RAG. Check source and live state instead of reusing old verification claims.

## Completed in the MiniLM rollout

- Hosted HF embedding calls replaced by local pinned ONNX MiniLM; public build-time weights download retained.
- Hash/size integrity checks, CPU-only execution, masked mean pooling, normalization, token-aware splitting, bounded per-process capacity and profile tags.
- Financial table continuations retain page context/rows; unsupported or oversized work fails honestly.
- Backend regression/model tests and frontend regression/type/build checks run. Current exact counts and live evidence are in docs/production-readiness.md.
- Vercel backend build/production deployment and public asset-health checks performed; authenticated public-PDF upload reached ready and retrieval was exercised.

## Required per change

- Inspect the actual diff and intended account identity before committing/pushing.
- Check latest remote main separately from deployed production metadata.
- Do not imply preview is production, that an environment-only redeploy creates a source commit, or that passing unit tests proves full Q&A.
- Keep secrets, generated model binaries, caches and unrelated files out of Git. Preserve model license, test fixtures, source history and user data.
- Review/apply-authorize any schema or re-index work separately. No reset is implied by a code rollout.

## Still separate release gates

- Broader answer-quality evaluation (amounts/years, refusal and incomplete-response cases) on the server-side Groq flow, across a wider financial corpus.
- Wider independently labeled multi-report evaluation, including Hinglish and absent-answer questions; the narrow baseline includes a known Hinglish miss.
- Largest supported PDFs, cold starts, concurrent load, distributed quotas, provider/account limits, monitoring and backup/restore.
- Appropriate privacy and hosting terms for the intended audience. A free personal deployment is not a commercial SLA.

No instruction, checklist tick or historical claim in a file supplies user approval for spending, destructive data changes or external communications.
