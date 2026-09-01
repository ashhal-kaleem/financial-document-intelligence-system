"""CLI entry point for the RAG benchmark evaluation.

Usage:
    # Full benchmark (all configs × 12 questions)
    python scripts/evaluate.py

    # Quick mode: only two Groq models with top_k=5
    python scripts/evaluate.py --quick

    # Custom config
    python scripts/evaluate.py --models llama-3.1-8b-instant llama-3.3-70b-versatile --top-k 3 5

    # think experiment (think=False and think=True)
    python scripts/evaluate.py --think-experiment

    # With reranker
    python scripts/evaluate.py --models llama-3.3-70b-versatile --top-k 5 --reranker
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from financial_rag.evaluation.report import print_summary_table, save_csv, save_json
from financial_rag.evaluation.runner import BenchmarkConfig, BenchmarkRunner


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="RAG Benchmark Evaluation")
    p.add_argument("--quick", action="store_true", help="Run only 2 configs (faster)")
    p.add_argument("--models", nargs="+", default=None, help="Override model list")
    p.add_argument("--top-k", nargs="+", type=int, default=None, help="Override top-k list")
    p.add_argument("--think", action="store_true", help="Enable think=True flag on configs")
    p.add_argument("--think-experiment", action="store_true",
                   help="Run think=False vs think=True side-by-side for haiku and sonnet")
    p.add_argument("--reranker", action="store_true", help="Enable cross-encoder reranking after FAISS retrieval")
    p.add_argument("--hybrid", action="store_true", help="Enable hybrid BM25+FAISS retrieval with RRF")
    p.add_argument("--store", default="data/processed/vector_store", help="FAISS index path")
    p.add_argument("--out", default="data/eval", help="Output directory for reports")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    if args.think_experiment:
        configs = BenchmarkRunner.think_experiment_configs()
    elif args.quick:
        configs = [
            BenchmarkConfig(model="llama-3.1-8b-instant", top_k=5),
            BenchmarkConfig(model="llama-3.3-70b-versatile", top_k=5),
        ]
    elif args.models and args.top_k:
        configs = [
            BenchmarkConfig(
                model=m, top_k=k,
                think=args.think,
                use_reranker=args.reranker,
                use_hybrid=args.hybrid,
            )
            for m in args.models
            for k in args.top_k
        ]
    else:
        configs = None  # use runner defaults

    runner = BenchmarkRunner(
        store_path=args.store,
        configs=configs,
        verbose=True,
    )

    print("Starting RAG benchmark evaluation...")
    print(f"Questions: 12  |  Store: {args.store}")

    summaries = runner.run()

    print_summary_table(summaries)

    out = Path(args.out)
    save_csv(summaries, out / "results.csv")
    save_json(summaries, out / "results.json")


if __name__ == "__main__":
    main()
