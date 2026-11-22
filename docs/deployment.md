# Deployment runbook

Revised 22 November 2026. The frontend and FastAPI backend use separate Vercel Hobby projects. Supabase holds auth, private PDFs and vectors. The old Render service stays suspended as a rollback option. A deployed app is not a production-acceptance certificate, and this file grants no account, data or spending authority.

## Backend build

```sh
cd backend
uv sync --frozen
uv run python scripts/fetch_embedding_model.py
uv run pytest -q
```

Use the FastAPI preset with the entrypoint in `pyproject.toml`. Its build script fetches public MiniLM weights at a fixed revision, checks sizes/SHA-256 and bundles them. `vercel.json` explicitly includes generated model assets, excludes test/virtualenv files and sets a 300-second maximum. Do not download weights during a user request, depend on warm caches or silently change model precision. Keep model attribution/license in the bundle.

No HF inference token, Cloudflare setup or paid embedding endpoint is needed. Supabase URL/service-role/anon settings, private bucket name, allowed frontend origins and auth flags remain necessary. Never expose the service role in a frontend variable or log. Vercel forces inline ingestion; use the queue worker only on a separately approved long-running host. Configure `MAX_UPLOAD_SIZE_BYTES=4194304` for the current 4 MiB app cap. The bucket's admission limit is separate.

Frontend configuration: `NEXT_PUBLIC_API_URL=https://fdis-backend.vercel.app/api/v1`, plus the existing Supabase public URL/anon key. Puter has its own explicit sign-in/consent flow and no backend account token.

## Hosted data

The existing project has migrations 0001-0004 from prior approved work. Never infer that another target is empty or compatible. Read current vector/document counts and schema before a model rollout. New chunks carry a model-profile tag; incompatible/missing tags on search results are rejected. Re-indexing existing vectors, destructive cleanup, schema changes and applying 0005 require their own approval. Keep original documents and useful rollback history.

Owner-isolation tests use fresh temporary test users and public test PDFs. Record created IDs privately and delete only that test data after checking owner reads/searches/deletes and cross-owner denial. Do not touch an existing errored user document as cleanup.

## Runtime limits

The published Fluid Hobby limits are 2 GB function memory and a 300-second maximum, with a standard Python bundle limit of 500 MB. Verify actual build output and deployment settings; a local footprint is not deployed size. The filesystem is read-only except ephemeral instance-local `/tmp`. The default 2,000-chunk cap, 45-second cooperative parser check and bounded encoder budget reduce work, but native operations cannot be forcibly interrupted by those checks. File size does not bound page count, tokens or table complexity. Large/slow PDFs must return a clear error or use a separately designed resumable pipeline.

The rate limiter/inference lock is per process, not a distributed quota. Free hosting and Puter allowances can pause or fail. No unlimited uptime, free-forever or business SLA claim is supported. Vercel Hobby is personal/noncommercial.

## Before committing or releasing

1. Verify the current remote head, working diff and expected author identity. Run tests, inspect each staged diff and exclude secrets, generated model binaries and unrelated changes. Push small meaningful commits.
2. Run backend tests with downloaded pinned assets, frontend regression tests/typecheck/build, and local migration regression tests when the migration contract is affected. Model tests must prove offline operation, dimensions, normalization, token bounds, corruption/missing-asset handling and reproducible doc/query vectors.
3. Build a preview, inspect its actual package/config and test its authenticated endpoints. Deploy production only under the established rollout scope. Confirm the production target's source hash separately from the latest commit and from a newer environment-only redeployment.
4. Test a public financial PDF through signed upload, ready status, owner retrieval with correct source pages, denied cross-owner reads/searches/deletes, failure states and owner deletion. Record exact source/amount/year retrieval checks. Citation-marker success is not semantic accuracy.
5. Treat actual Puter model generation as a separate authorized check. The allowlist uses catalog-verified zero-priced variants and no paid fallback, but availability/account limits remain external. Do not claim full Q&A works if only retrieval/receipt plumbing was tested.
6. Confirm only test data was removed and the original data/configuration remain. Report pushed, deployed, tested and pending facts separately with current hashes and dates.

## Sources

- https://vercel.com/docs/frameworks/backend/fastapi
- https://vercel.com/docs/functions/runtimes/python
- https://vercel.com/docs/functions/limitations
- https://vercel.com/docs/functions/runtimes
- https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
- https://docs.puter.com/user-pays-model/
- https://docs.puter.com/rate-limits-and-quotas/
