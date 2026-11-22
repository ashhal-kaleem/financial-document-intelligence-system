# Current project map

Updated 22 November 2026. This is an orientation note, not live account state or execution approval.

FDIS remains the same financial-document RAG project: private PDF upload, source passage retrieval, cited answers and authenticated PDF inspection. The embedding implementation changed, not the product idea.

- Source is on main. Verify the current remote HEAD before reporting it as latest.
- Frontend and FastAPI backend use separate Vercel Hobby projects; Supabase holds auth, private PDFs and vectors. The former Render service is preserved, suspended.
- MiniLM public model weights are pulled from a pinned HF revision at build time and run in our backend with ONNX Runtime. Hosted HF inference and HF_TOKEN are removed. No Cloudflare integration was added.
- Answers are written server-side on the Groq free plan (`openai/gpt-oss-120b`, key server-only). The free daily quota is a real cap, not an unlimited-free guarantee.
- Existing app data is not repository documentation. Updating old Markdown files does not authorize deleting uploaded PDFs, rows, accounts, models or migrations.

Start with README.md for product/setup, docs/architecture.md for data flow, docs/deployment.md for deployment controls and docs/production-readiness.md for measured evidence versus open gates. This file does not duplicate changing test counts or deployment hashes.

The verified GitHub credential identity on 22 November was ashhal-kaleem. Check it again when needed; old profile/author names do not override the actual intended account. Review diffs, test small changes and distinguish committed, pushed, deployed and tested.
