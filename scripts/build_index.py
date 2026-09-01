"""Rebuild the FAISS vector index from source documents.

Usage:
    # Default config (matches settings.py defaults)
    python scripts/build_index.py

    # Custom chunk config
    python scripts/build_index.py --chunk-size 800 --chunk-overlap 100

    # Custom data dir and output path
    python scripts/build_index.py --data-dir data/samples --out data/processed/vector_store
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from financial_rag.chunking.splitter import RecursiveCharacterSplitter
from financial_rag.embeddings.sentence_transformer import SentenceTransformerEmbedder
from financial_rag.ingestion.factory import load_directory
from financial_rag.retrieval.vector_store import FAISSVectorStore


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build FAISS index from source documents")
    p.add_argument("--data-dir", default="data/samples", help="Directory with source documents")
    p.add_argument("--out", default="data/processed/vector_store", help="Output path (no extension)")
    p.add_argument("--chunk-size", type=int, default=512, help="Max characters per chunk")
    p.add_argument("--chunk-overlap", type=int, default=64, help="Overlap characters between chunks")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    print(f"chunk_size={args.chunk_size}  chunk_overlap={args.chunk_overlap}")
    print(f"data_dir={args.data_dir}  out={args.out}\n")

    print("Loading documents...")
    documents = load_directory(args.data_dir)
    print(f"  {len(documents)} page(s) loaded\n")

    print("Chunking...")
    splitter = RecursiveCharacterSplitter(
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )
    chunks = splitter.split_documents(documents)
    print(f"  {len(chunks)} chunks produced\n")

    print("Loading embedder...")
    embedder = SentenceTransformerEmbedder()

    print("Building FAISS index...")
    store = FAISSVectorStore(dimension=embedder.dimension)
    store.add_chunks(chunks, embedder)

    print("Saving index...")
    store.save(args.out)
    print(f"\nDone. Index saved to {args.out}.*")
    print(f"  chunks={store.size}  dim={store.dimension}")


if __name__ == "__main__":
    main()
