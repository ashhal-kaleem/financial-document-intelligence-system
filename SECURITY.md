# Security status

No public security contact or response-time commitment has been configured. Use the repository owner's established private contact for sensitive reports; do not post secrets in public issues.

## Current code controls

- Supabase user token verification; owner-scoped reads and writes; shared samples read-only.
- Authenticated file reads, private no-store responses, no client service-role/provider keys.
- Upload and ask request limits are per user, in memory per process, bounded to 1000 active accounts. This is not a distributed spending quota.
- Provider model allowlist, output cap, opt-in fallback, strict stream failure handling.
- Citation markers must refer to retrieved sources. This does not prove semantic accuracy.
- Untrusted passages are identified in the prompt. This does not prove injection resistance.
- Browser-local histories use account-specific keys. The unscoped legacy key is discarded rather than attributed to a user. Browser storage is not encrypted, and is not cross-device persistence.
- Open notify relay removed; CORS is configured; raw provider errors are not returned as answers.

## Release gaps

Private bucket and working login need hosted setup. Live two-user isolation, full deletion and crash recovery need separate target/usage approval. Migration 0004 is a new, unapplied two-phase deletion proposal. Deploying the new deletion code without it will fail closed, not silently leave files behind. Busy uploads/processing cannot be deleted until settled. Storage failures retain a deleting row for retry; no success is shown before both systems confirm.

No real provider quality/cost, dependency audit, production observability or backup/restore drill is claimed. See docs/production-readiness.md and deployment.md. Rotate exposed keys through the provider, not through committed files.
