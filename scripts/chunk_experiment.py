"""Chunk configuration experiment — finds the best chunk_size/overlap for retrieval.

Rebuilds the FAISS index in-memory for each config and measures Recall@k + MRR
without any LLM call. Runs in ~30 seconds vs ~30 minutes for a full LLM eval.

Usage:
    python scripts/chunk_experiment.py
    python scripts/chunk_experiment.py --data-dir data/samples --top-k 3 5
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from financial_rag.chunking.splitter import RecursiveCharacterSplitter
from financial_rag.embeddings.sentence_transformer import SentenceTransformerEmbedder
from financial_rag.evaluation.retrieval_bench import (
    ChunkConfig,
    RetrievalBenchResult,
    run_retrieval_bench,
    print_bench_table,
)
from financial_rag.ingestion.factory import load_directory
from financial_rag.retrieval.retriever import VectorRetriever
from financial_rag.retrieval.vector_store import FAISSVectorStore


CHUNK_CONFIGS: list[ChunkConfig] = [
    ChunkConfig(label="baseline (512/64)",  chunk_size=512,  chunk_overlap=64),
    ChunkConfig(label="overlap+ (512/128)", chunk_size=512,  chunk_overlap=128),
    ChunkConfig(label="medium (800/100)",   chunk_size=800,  chunk_overlap=100),
    ChunkConfig(label="medium+ (800/200)",  chunk_size=800,  chunk_overlap=200),
    ChunkConfig(label="large (1024/150)",   chunk_size=1024, chunk_overlap=150),
]


def build_retriever(
    documents,
    embedder: SentenceTransformerEmbedder,
    chunk_size: int,
    chunk_overlap: int,
) -> VectorRetriever:
    splitter = RecursiveCharacterSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    chunks = splitter.split_documents(documents)

    store = FAISSVectorStore(dimension=embedder.dimension)
    store.add_chunks(chunks, embedder)

    return VectorRetriever(store=store, embedder=embedder, score_threshold=0.0)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Chunk configuration experiment")
    p.add_argument("--data-dir", default="data/samples", help="Directory with source documents")
    p.add_argument("--top-k", nargs="+", type=int, default=[3, 5], help="top_k values to test")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    print(f"Loading documents from {args.data_dir}...")
    documents = load_directory(args.data_dir)
    print(f"  {len(documents)} page(s) loaded\n")

    print("Loading embedder (one-time)...")
    embedder = SentenceTransformerEmbedder()
    print(f"  {embedder}\n")

    all_results: list[RetrievalBenchResult] = []

    for config in CHUNK_CONFIGS:
        print(f"Building index: {config.label}  (size={config.chunk_size}, overlap={config.chunk_overlap})")
        retriever = build_retriever(documents, embedder, config.chunk_size, config.chunk_overlap)
        print(f"  {retriever.store_size} chunks indexed")

        for top_k in args.top_k:
            result = run_retrieval_bench(retriever, config, top_k=top_k)
            all_results.append(result)
            print(f"  top_k={top_k}  Recall={result.recall_at_k():.1%}  MRR={result.mrr():.3f}  avg_score={result.avg_top_score():.4f}")

        print()

    print_bench_table(all_results)
    print("\nNext step: run the full LLM eval on the winning config.")
    print("  python scripts/evaluate.py --models llama-3.1-8b-instant --top-k <best_k> --store <rebuilt_index>")


if __name__ == "__main__":
    main()
