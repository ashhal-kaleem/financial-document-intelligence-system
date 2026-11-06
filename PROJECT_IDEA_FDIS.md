# FDIS product vision

Build a private financial-report workspace for analysts, auditors and investors: upload a text-based corporate PDF, ask a question, inspect the source passage and verify the page citation.

V1 is document-grounded Q&A, not a trading or investment recommendation system. Preserve financial units, currency, year and reporting basis; decline to invent missing facts. Prompt instructions alone cannot guarantee correctness.

Core flow: authenticate → upload → durable processing → ready document → scoped retrieval → streamed answer → inspect page evidence → delete when needed.

Current code uses Next.js/React, FastAPI, PyMuPDF, Supabase PostgreSQL/pgvector, and configurable embedding/inference providers. Package files, source and reviewed migrations define implementation, not older spec version numbers or provider names.

Later candidates: OCR, structured extraction, multi-report comparisons, saved conversations and team access. Add these after measured evidence supports the basic flow.

No project credentials belong here. See .env.example files, README.md and docs/deployment.md for setup. Model access, costs, quality and deployment state require current verification.
