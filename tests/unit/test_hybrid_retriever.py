"""Unit tests for the HybridRetriever (BM25 + FAISS with RRF)."""

import pytest
from unittest.mock import MagicMock

from financial_rag.chunking.models import Chunk
from financial_rag.retrieval.hybrid import HybridRetriever, _BM25Index
from financial_rag.retrieval.vector_store import SearchResult


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_chunk(idx: int, content: str, source: str = "test.pdf") -> Chunk:
    return Chunk(
        content=content,
        source=source,
        page=idx,
        chunk_index=idx,
        total_chunks=10,
        metadata={},
    )


def _make_search_result(chunk: Chunk, score: float, rank: int) -> SearchResult:
    return SearchResult(chunk=chunk, score=score, rank=rank)


def _make_mock_store(chunks: list[Chunk]) -> MagicMock:
    store = MagicMock()
    store.chunks = chunks
    store.size = len(chunks)
    store.search.return_value = [
        _make_search_result(c, score=0.9 - i * 0.1, rank=i)
        for i, c in enumerate(chunks)
    ]
    return store


# ── _BM25Index ────────────────────────────────────────────────────────────────

class TestBM25Index:
    def test_returns_top_k_results(self):
        chunks = [_make_chunk(i, f"utilidad neta interbank {i}") for i in range(10)]
        idx = _BM25Index(chunks=chunks)
        results = idx.query("utilidad neta", top_k=3)
        assert len(results) == 3

    def test_scores_are_sorted_descending(self):
        chunks = [_make_chunk(i, f"utilidad neta interbank {i}") for i in range(5)]
        idx = _BM25Index(chunks=chunks)
        results = idx.query("utilidad", top_k=5)
        scores = [s for _, s in results]
        assert scores == sorted(scores, reverse=True)

    def test_exact_match_ranks_higher(self):
        chunks = [
            _make_chunk(0, "empleados de interbank 2024"),
            _make_chunk(1, "política de dividendos scotiabank"),
            _make_chunk(2, "número de empleados en el banco"),
        ]
        idx = _BM25Index(chunks=chunks)
        results = idx.query("empleados interbank", top_k=3)
        top_chunk_idx = results[0][0]
        assert top_chunk_idx == 0  # exact match chunk ranks first

    def test_empty_corpus(self):
        idx = _BM25Index(chunks=[])
        results = idx.query("cualquier cosa", top_k=5)
        assert results == []


# ── HybridRetriever ───────────────────────────────────────────────────────────

class TestHybridRetriever:
    def _make_retriever(self, chunks: list[Chunk]) -> HybridRetriever:
        store = _make_mock_store(chunks)
        embedder = MagicMock()
        return HybridRetriever(store=store, embedder=embedder)

    def test_returns_retrieval_result(self):
        from financial_rag.retrieval.models import RetrievalResult
        chunks = [_make_chunk(i, f"texto del chunk {i}") for i in range(5)]
        retriever = self._make_retriever(chunks)
        result = retriever.retrieve("query", top_k=3)
        assert isinstance(result, RetrievalResult)

    def test_returns_at_most_top_k(self):
        chunks = [_make_chunk(i, f"chunk {i}") for i in range(10)]
        retriever = self._make_retriever(chunks)
        result = retriever.retrieve("query", top_k=4)
        assert len(result.results) <= 4

    def test_ranks_are_sequential(self):
        chunks = [_make_chunk(i, f"chunk {i}") for i in range(5)]
        retriever = self._make_retriever(chunks)
        result = retriever.retrieve("query", top_k=3)
        assert [r.rank for r in result.results] == list(range(len(result.results)))

    def test_source_filter_applied(self):
        chunks = [
            _make_chunk(0, "datos interbank", source="interbank.pdf"),
            _make_chunk(1, "datos scotiabank", source="scotiabank.pdf"),
            _make_chunk(2, "más interbank", source="interbank.pdf"),
        ]
        store = _make_mock_store(chunks)
        store.search.return_value = [
            _make_search_result(c, score=0.9 - i * 0.1, rank=i)
            for i, c in enumerate(chunks)
        ]
        retriever = HybridRetriever(store=store, embedder=MagicMock())
        result = retriever.retrieve("query", top_k=5, source_filter="scotiabank")
        assert all("scotiabank" in r.chunk.source.lower() for r in result.results)

    def test_source_filter_returns_top_k_when_available(self):
        """Filter must not silently truncate results when enough matching chunks exist."""
        chunks = (
            [_make_chunk(i, f"datos interbank {i}", source="interbank.pdf") for i in range(3)]
            + [_make_chunk(i + 3, f"datos scotiabank {i}", source="scotiabank.pdf") for i in range(6)]
        )
        store = _make_mock_store(chunks)
        store.size = len(chunks)
        store.search.return_value = [
            _make_search_result(c, score=0.9 - i * 0.05, rank=i)
            for i, c in enumerate(chunks)
        ]
        retriever = HybridRetriever(store=store, embedder=MagicMock())
        result = retriever.retrieve("query", top_k=5, source_filter="scotiabank")
        assert len(result.results) == 5
        assert all("scotiabank" in r.chunk.source.lower() for r in result.results)

    def test_no_collision_across_sources_with_same_chunk_index(self):
        """Chunks from different documents sharing chunk_index must not collide in RRF.

        Before the fix, (source_A, chunk_index=0) and (source_B, chunk_index=0)
        both mapped to key 0 in the RRF dict — one chunk was silently lost or got
        the wrong score. The compound (source, chunk_index) key prevents this.
        """
        # Two banks, each with 3 chunks. Both sets use chunk_index 0, 1, 2.
        interbank = [
            _make_chunk(i, f"interbank datos {i}", source="interbank.pdf")
            for i in range(3)
        ]
        scotiabank = [
            _make_chunk(i, f"scotiabank datos {i}", source="scotiabank.pdf")
            for i in range(3)
        ]
        all_chunks = interbank + scotiabank

        store = _make_mock_store(all_chunks)
        store.size = len(all_chunks)
        store.search.return_value = [
            _make_search_result(c, score=0.9 - i * 0.05, rank=i)
            for i, c in enumerate(all_chunks)
        ]

        retriever = HybridRetriever(store=store, embedder=MagicMock())
        result = retriever.retrieve("query", top_k=6)

        assert len(result.results) == 6, (
            "All 6 chunks must survive RRF — collision shrinks this to 3"
        )
        sources = {r.chunk.source for r in result.results}
        assert "interbank.pdf" in sources
        assert "scotiabank.pdf" in sources

    def test_repr(self):
        chunks = [_make_chunk(0, "texto")]
        retriever = self._make_retriever(chunks)
        assert "HybridRetriever" in repr(retriever)
        assert "rrf_k" in repr(retriever)

    def test_store_size_property(self):
        chunks = [_make_chunk(i, f"chunk {i}") for i in range(7)]
        retriever = self._make_retriever(chunks)
        assert retriever.store_size == 7
