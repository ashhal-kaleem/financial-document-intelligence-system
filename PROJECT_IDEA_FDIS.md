# Financial-document RAG: unchanged product idea

FDIS is a private financial-report workspace, not a generic chatbot and not an investment-advice engine.

The flow remains: sign in, upload a text-based corporate PDF, wait for honest processing status, ask a document-specific question, inspect the retrieved source passage/page and delete a document when appropriate.

RAG means the app retrieves relevant passages from uploaded documents before asking a language model to write an answer. MiniLM now creates the search vectors inside the backend. Puter provides the opt-in answer-writing model. Downloading free public weights from HF is different from using its hosted inference API.

V1 priorities are owner isolation, recovery from failed processing, preservation of currency/units/years/reporting basis, source citations and clear limits. A valid citation marker alone does not prove the answer is financially correct. No-source questions must not invent evidence.

OCR, structured financial extraction, cross-report analytics, team access and cross-device conversation sync remain future work unless independently implemented and tested. The current browser history is local to the browser/account/document.

Use docs/PRD.md for required behavior and docs/production-readiness.md for evidence. This idea note does not make deployment, model quality, price or uptime claims.
