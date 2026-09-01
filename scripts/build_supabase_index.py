"""Build the Supabase pgvector index from source documents.

Usage:
    python scripts/build_supabase_index.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Fix Windows console encoding so Unicode arrows in log lines don't crash.
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]

from dotenv import load_dotenv

# Make src importable
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from financial_rag.chunking.splitter import RecursiveCharacterSplitter
from financial_rag.embeddings.sentence_transformer import SentenceTransformerEmbedder
from financial_rag.ingestion.factory import load_directory
from financial_rag.retrieval.supabase_vector_store import SupabaseVectorStore


def main() -> None:
    load_dotenv(ROOT / ".env")

    supabase_url = os.getenv("SUPABASE_URL", "")
    supabase_key = os.getenv("SUPABASE_KEY", "")
    table = os.getenv("SUPABASE_TABLE", "chunks")
    rpc_fn = os.getenv("SUPABASE_RPC", "match_chunks")
    model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    if not supabase_url:
        raise RuntimeError("SUPABASE_URL is missing from .env")

    if not supabase_key:
        raise RuntimeError("SUPABASE_KEY is missing from .env")

    data_dir = ROOT / "data" / "samples"

    print("=" * 60)
    print("  SUPABASE VECTOR INDEX BUILDER")
    print("=" * 60)
    print(f"Data directory : {data_dir}")
    print(f"Supabase table : {table}")
    print(f"RPC function   : {rpc_fn}")
    print(f"Embedding model: {model_name}")
    print()

    # ---------------------------------------------------------
    # 1. Load documents
    # ---------------------------------------------------------
    print("[1/4] Loading documents...")

    documents = load_directory(data_dir)

    print(f"\n  Loaded {len(documents)} document/page objects.")

    if not documents:
        raise RuntimeError("No documents were loaded from data/samples.")

    # ---------------------------------------------------------
    # 2. Chunk documents
    # ---------------------------------------------------------
    print("\n[2/4] Chunking documents...")

    splitter = RecursiveCharacterSplitter(
        chunk_size=512,
        chunk_overlap=64,
    )

    chunks = splitter.split_documents(documents)

    print(f"  Created {len(chunks)} chunks.")

    if not chunks:
        raise RuntimeError("No chunks were created.")

    # Show document distribution
    counts: dict[str, int] = {}

    for chunk in chunks:
        counts[chunk.filename] = counts.get(chunk.filename, 0) + 1

    print("\n  Chunks by document:")
    for filename, count in counts.items():
        print(f"    {filename}: {count}")

    # ---------------------------------------------------------
    # 3. Create embedder
    # ---------------------------------------------------------
    print("\n[3/4] Loading embedding model...")

    embedder = SentenceTransformerEmbedder(
        model_name=model_name,
        batch_size=64,
        show_progress=True,
    )

    print(f"  Embedding dimension: {embedder.dimension}")

    if embedder.dimension != 384:
        raise RuntimeError(
            f"Expected 384-dimensional embeddings, "
            f"but model produced {embedder.dimension}."
        )

    # ---------------------------------------------------------
    # 4. Insert into Supabase
    # ---------------------------------------------------------
    print("\n[4/4] Uploading chunks to Supabase...")

    store = SupabaseVectorStore(
        supabase_url=supabase_url,
        supabase_key=supabase_key,
        table=table,
        rpc_fn=rpc_fn,
    )

    # --- Clear existing rows BEFORE embedding so a failure leaves the table
    # empty rather than mixing old and new chunks.
    existing = store.size
    print(f"  Clearing {existing} existing row(s) from '{table}'...")
    store.clear()
    print(f"  Table cleared. Inserting {len(chunks)} new chunks...")

    store.add_chunks(chunks, embedder)

    final_size = store.size
    print("\n" + "=" * 60)
    print("  INDEXING COMPLETE")
    print("=" * 60)
    print(f"  Documents/pages : {len(documents)}")
    print(f"  Chunks inserted : {len(chunks)}")
    print(f"  Supabase rows   : {final_size}")
    print(f"  Embedding dim   : {embedder.dimension}")
    print("=" * 60)


if __name__ == "__main__":
    main()