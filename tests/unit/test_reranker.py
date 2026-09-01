"""Unit tests for the re-ranker components and pipeline integration."""

import pytest

from financial_rag.chunking.splitter import Chunk
from financial_rag.retrieval.reranker import MockReranker
from financial_rag.retrieval.vector_store import SearchResult


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_result(rank: int, score: float, content: str = "text") -> SearchResult:
    chunk = Chunk(
        content=content,
        source="test.pdf",
        page=rank,
        chunk_index=rank,
        total_chunks=5,
        metadata={},
    )
    return SearchResult(chunk=chunk, score=score, rank=rank)


# ── MockReranker ──────────────────────────────────────────────────────────────

class TestMockReranker:
    def test_returns_top_k(self):
        results = [_make_result(i, 0.9 - i * 0.1) for i in range(5)]
        reranker = MockReranker()
        out = reranker.rerank("query", results, top_k=3)
        assert len(out) == 3

    def test_preserves_order(self):
        results = [_make_result(i, 0.9 - i * 0.1, content=f"chunk {i}") for i in range(4)]
        reranker = MockReranker()
        out = reranker.rerank("query", results, top_k=3)
        assert [r.chunk.content for r in out] == ["chunk 0", "chunk 1", "chunk 2"]

    def test_empty_input_returns_empty(self):
        reranker = MockReranker()
        assert reranker.rerank("query", [], top_k=5) == []

    def test_top_k_larger_than_results(self):
        results = [_make_result(i, 0.5) for i in range(2)]
        reranker = MockReranker()
        out = reranker.rerank("query", results, top_k=10)
        assert len(out) == 2

    def test_ranks_updated(self):
        results = [_make_result(i, 0.5) for i in range(3)]
        reranker = MockReranker()
        out = reranker.rerank("query", results, top_k=3)
        assert [r.rank for r in out] == [0, 1, 2]



# ── BenchmarkConfig with reranker ─────────────────────────────────────────────

class TestBenchmarkConfigReranker:
    def test_use_reranker_defaults_false(self):
        from financial_rag.evaluation.runner import BenchmarkConfig
        cfg = BenchmarkConfig(model="llama-3.3-70b-versatile", top_k=5)
        assert cfg.use_reranker is False

    def test_use_reranker_can_be_set(self):
        from financial_rag.evaluation.runner import BenchmarkConfig
        cfg = BenchmarkConfig(model="llama-3.3-70b-versatile", top_k=5, use_reranker=True)
        assert cfg.use_reranker is True
