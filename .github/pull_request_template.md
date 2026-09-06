# Pull Request

## Description
[Brief summary of changes and user impact]

## Related Specifications
- Ref: `docs/PRD.md`
- Ref: `docs/architecture.md`
- Ref: `docs/api-docs.md`

## Verification Checklist
- [ ] Backend tests pass (`uv run pytest -v`)
- [ ] Frontend typechecks cleanly (`pnpm run typecheck`)
- [ ] No server credentials leaked in frontend (`grep -rn "API_KEY\|SECRET" frontend/src/`)
- [ ] Follows strict 4-tier one-way dependency rule
