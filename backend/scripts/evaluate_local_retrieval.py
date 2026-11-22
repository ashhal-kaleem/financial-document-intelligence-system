"""Run a local, single-page retrieval sanity set. Never calls Puter/hosted APIs.

From backend, after fetching/verifying the pinned model:
    uv run python scripts/evaluate_local_retrieval.py

This authored expected-number test is NOT answer accuracy, semantic support,
multilingual assurance or an independently labeled benchmark. Number presence
in a top-five passage is weaker than proving the right financial row/period.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.infrastructure.embedding_client import EmbeddingClient  # noqa: E402


def main() -> None:
    fixture_dir = ROOT / "tests" / "evaluation"
    fixture = json.loads((fixture_dir / "apple-fy25-q4-page1-chunks.json").read_text())
    cases = json.loads((fixture_dir / "apple-fy25-q4-page1-cases.json").read_text())
    texts = [chunk["content"] for chunk in fixture["chunks"]]
    client = EmbeddingClient()
    vectors = client.embed_texts(texts)
    results = []
    for question, expected in cases:
        query = client.embed_query(question)
        scores = [sum(a * b for a, b in zip(vector, query, strict=True)) for vector in vectors]
        indices = sorted(range(len(texts)), key=lambda i: scores[i], reverse=True)[:5]
        ranks = [rank for rank, i in enumerate(indices, start=1) if expected in texts[i]]
        results.append({"question": question, "expected": expected, "hit_at_5": bool(ranks), "ranks": ranks})
    hits = sum(result["hit_at_5"] for result in results)
    print(json.dumps({
        "source": fixture["source"], "page": fixture["page"], "chunks": len(texts),
        "scope": fixture["scope"], "metric": "expected-number presence in top-five local passages",
        "hits": hits, "cases": len(results), "results": results,
    }, indent=2))


if __name__ == "__main__":
    main()
