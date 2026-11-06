> Historical planning/status record. For current implementation and open gates see README.md and docs/production-readiness.md. Old verification and feature claims below are not a live production certificate.

# Test strategy

Use README.md for exact offline commands and docs/production-readiness.md for evidence limits. tests/test_financial_seed.py checks synthetic PDF/evidence plumbing, not model quality. frontend/tests/regressions.test.cjs uses Node's test runner and the pinned TypeScript transpiler, without live services.

Live tests default to skipped. RUN_LIVE_TESTS=1 is an explicit switch, not authority: first get an isolated empty project, permitted test users/storage mutations and bounded provider usage. Never use private documents or enable production test writes by accident.

Required release evidence: login/upload/PDF/answer/delete; two-user isolation including selected-document search; queue crash/restart and lost-worker writes; provider429/timeouts/truncated streams; financial numeric/citation support/abstention/injection benchmark; privacy settings; measured latency and cost; backup/restore. Record failures and exact configurations. Do not use an empty queue check as proof of recovery.
