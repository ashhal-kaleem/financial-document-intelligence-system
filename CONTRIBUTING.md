# Contributing Guidelines — Financial Document Intelligence System (FDIS)

1. **Branching**: Use `feat/feature-name` or `fix/bug-name`.
2. **Commit Messages**: Conventional commits (`feat: add citation drawer`, `fix: handle empty pdf`).
3. **One-Way Architecture**: Respect `Router` -> `Service` -> `Domain` -> `Infrastructure`.
4. **Verification**: Run `uv run pytest -v` and `pnpm run typecheck` before submitting PRs.
