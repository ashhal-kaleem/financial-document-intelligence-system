# Test map and evidence rules

Updated 22 November 2026. Tests stay in the repository; this note is not the test implementation.

## Reproduce

```sh
cd backend
uv sync --frozen
uv run python scripts/fetch_embedding_model.py
uv run pytest -q
cd ../frontend
pnpm install --frozen-lockfile  # use pnpm 9, matching CI/lockfile
node --test tests/*.test.cjs
pnpm typecheck
pnpm build
```

Backend tests cover auth/document scoping, storage/ingestion failures, queue fencing, citation rules, local vector dimensions/norms, offline operation, token splitting, deterministic doc/query encoding, profile mismatches and bounded work. CI downloads pinned public model assets before running tests. No user document is sent to HF inference.

The bundled sample_apple_10k.pdf and financial_seed.json are synthetic test fixtures. They are not private uploads or independently labeled model-accuracy evidence. Keep them unless their dependent tests are intentionally replaced.

scripts/test_migrations.py uses throwaway local Postgres and role/auth stubs; it is not a hosted migration or storage test. Existing live suites remain opt-in. RUN_LIVE_TESTS=1 is a switch, not permission to write production data or spend quota.

The public Apple statement retrieval check is separate from actual language-model generation. Its narrow result, known Hinglish miss and limitations are in production-readiness.md. Broader financial accuracy, absent-answer behavior and hostile-document resistance remain separate gates.

For live checks use approved temporary users and public documents, record created IDs privately, test both owners and negative access, then remove only test data. Preserve existing app documents and metadata unless specifically approved otherwise. Do not log tokens or put private reports in fixtures.
