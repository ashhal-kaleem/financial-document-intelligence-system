"""FAISS-backed vector store for chunk retrieval."""

import pickle
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from financial_rag.chunking.models import Chunk
from financial_rag.embeddings.base import BaseEmbedder


@dataclass
class SearchResult:
    """A single result from a vector similarity search."""

    chunk: Chunk
    score: float      # cosine similarity in [0, 1] — higher is more relevant
    rank: int         # position in result list (0 = most relevant)

    @property
    def citation(self) -> str:
        return self.chunk.citation

    def __repr__(self) -> str:
        return (
            f"SearchResult(rank={self.rank}, score={self.score:.3f}, "
            f"citation={self.citation!r})"
        )


class FAISSVectorStore:
    """Stores chunk embeddings in a FAISS index and supports similarity search.

    Uses IndexFlatIP (inner product) with L2-normalized vectors, which is
    mathematically equivalent to cosine similarity. Exact search — no
    approximation — appropriate for up to ~100k chunks.

    Args:
        dimension: Embedding vector size. Must match the embedder used.
    """

    def __init__(self, dimension: int) -> None:
        self.dimension = dimension
        self._index = None
        self._chunks: list[Chunk] = []

    # ── Building the index ────────────────────────────────────────────────

    def add_chunks(self, chunks: list[Chunk], embedder: BaseEmbedder) -> None:
        """Embed chunks and add them to the FAISS index.

        Args:
            chunks: Chunks to index.
            embedder: Embedder to use. Must produce vectors of self.dimension.
        """
        if not chunks:
            return

        import faiss

        if self._index is None:
            self._index = faiss.IndexFlatIP(self.dimension)

        texts = [chunk.content for chunk in chunks]
        vectors = embedder.embed(texts)  # already normalized by embedder contract

        self._index.add(vectors)
        self._chunks.extend(chunks)
        print(f"  [vector store] Indexed {len(chunks)} chunks. Total: {len(self._chunks)}")

    # ── Searching ─────────────────────────────────────────────────────────

    def search(
        self,
        query: str,
        embedder: BaseEmbedder,
        top_k: int = 5,
        score_threshold: float = 0.0,
        document_ids: list[str] | None = None,
    ) -> list[SearchResult]:
        """Find the most relevant chunks for a query.

        Args:
            query: Natural language question.
            embedder: Must be the same model used during indexing.
            top_k: Number of results to return.
            score_threshold: Minimum cosine similarity to include a result.

        Returns:
            List of SearchResult ordered by descending similarity score.
        """
        if self._index is None or len(self._chunks) == 0:
            return []

        query_vector = embedder.embed_query(query).reshape(1, -1)
        k = min(top_k, len(self._chunks))

        scores, indices = self._index.search(query_vector, k)

        results: list[SearchResult] = []
        for rank, (idx, score) in enumerate(zip(indices[0], scores[0])):
            if idx == -1:  # FAISS sentinel for "not enough results"
                continue
            score = float(score)
            if score < score_threshold:
                continue
            chunk = self._chunks[idx]
            if document_ids is not None:
                if chunk.metadata.get("document_id") not in document_ids:
                    continue
            results.append(
                SearchResult(chunk=chunk, score=score, rank=rank)
            )

        return results

    # ── Persistence ───────────────────────────────────────────────────────

    def save(self, path: str | Path) -> None:
        """Persist the index and chunk metadata to disk.

        Creates two files:
            <path>.faiss  — the FAISS binary index
            <path>.pkl    — pickled list of Chunk objects
        """
        import faiss

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        faiss.write_index(self._index, str(path.with_suffix(".faiss")))
        with open(path.with_suffix(".pkl"), "wb") as f:
            pickle.dump(self._chunks, f)

        print(f"  [vector store] Saved {len(self._chunks)} chunks → {path.parent}/")

    @classmethod
    def load(cls, path: str | Path) -> "FAISSVectorStore":
        """Load a previously saved index from disk.

        Args:
            path: Base path (without extension) used when saving.

        Returns:
            Loaded FAISSVectorStore ready for search.
        """
        import faiss

        path = Path(path)
        index = faiss.read_index(str(path.with_suffix(".faiss")))

        with open(path.with_suffix(".pkl"), "rb") as f:
            chunks: list[Chunk] = pickle.load(f)

        store = cls(dimension=index.d)
        store._index = index
        store._chunks = chunks
        print(f"  [vector store] Loaded {len(chunks)} chunks from {path.parent}/")
        return store

    # ── Properties ────────────────────────────────────────────────────────

    @property
    def chunks(self) -> list[Chunk]:
        """All chunks in the index (read-only view)."""
        return self._chunks

    @property
    def size(self) -> int:
        """Number of chunks currently indexed."""
        return len(self._chunks)

    @property
    def is_empty(self) -> bool:
        return self.size == 0

    def __repr__(self) -> str:
        return f"FAISSVectorStore(dimension={self.dimension}, chunks={self.size})"
