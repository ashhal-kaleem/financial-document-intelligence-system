"""Targeted retrieval diagnostic for the HBL ROE query.

Run after re-applying the Supabase SQL fix (English text config):

    python scripts/diagnose_hbl_roe.py

Prints the top-5 chunks returned for the HBL ROE question and whether the
relevant chunk (containing "Return on Equity" or "ROE" for HBL) appears.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from financial_rag.embeddings.sentence_transformer import SentenceTransformerEmbedder
from financial_rag.retrieval.supabase_vector_store import SupabaseVectorStore
from financial_rag.retrieval.retriever import VectorRetriever

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
TABLE        = os.getenv("SUPABASE_TABLE", "chunks")
RPC_FN       = os.getenv("SUPABASE_RPC",  "match_chunks_hybrid")
MODEL        = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# Queries to test — these all failed or were borderline in the E2E run
TEST_QUERIES = [
    "What is HBL's Return on Equity?",
    "What is the ROE for HBL?",
    "HBL ROE 2025",
    "Return on equity HBL annual report",
]

RELEVANCE_KEYWORDS = ["return on equity", "roe", "shareholders"]


def chunk_is_relevant(content: str) -> bool:
    lower = content.lower()
    return any(kw in lower for kw in RELEVANCE_KEYWORDS)


def main() -> None:
    print("=" * 60)
    print("  HBL ROE RETRIEVAL DIAGNOSTIC")
    print("=" * 60)
    print(f"RPC: {RPC_FN}  |  Table: {TABLE}  |  Embedder: {MODEL}\n")

    embedder = SentenceTransformerEmbedder(model_name=MODEL, show_progress=False)
    store = SupabaseVectorStore(SUPABASE_URL, SUPABASE_KEY, table=TABLE, rpc_fn=RPC_FN)
    retriever = VectorRetriever(store=store, embedder=embedder, score_threshold=0.0)

    passed = 0
    for query in TEST_QUERIES:
        result = retriever.retrieve(query, top_k=5)
        hit = any(chunk_is_relevant(r.chunk.content) for r in result.results)
        status = "PASS" if hit else "FAIL"
        if hit:
            passed += 1
        print(f"[{status}] {query!r}")
        for i, r in enumerate(result.results, 1):
            marker = " <-- RELEVANT" if chunk_is_relevant(r.chunk.content) else ""
            src = Path(r.chunk.source).name
            preview = r.chunk.content[:80].replace("\n", " ")
            print(f"  {i}. [{r.score:.3f}] {src} | {preview}{marker}")
        print()

    print(f"Result: {passed}/{len(TEST_QUERIES)} queries retrieved a relevant chunk in top-5")
    print()
    print("If this is still failing after re-applying the SQL fix:")
    print("  1. Open Supabase SQL Editor and run the updated match_chunks_hybrid from")
    print("     scripts/supabase_schema.sql (the CREATE OR REPLACE block for 4b).")
    print("  2. Verify the HBL PDF was chunked with ROE content:")
    print("     grep -i 'return on equity' data/samples/HBL_Annual_Report_2025.pdf")


if __name__ == "__main__":
    main()
