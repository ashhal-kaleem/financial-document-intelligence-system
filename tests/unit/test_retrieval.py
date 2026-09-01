"""Unit tests for VectorRetriever and RetrievalResult."""

import pytest

from financial_rag.chunking.models import Chunk
from financial_rag.embeddings.mock import MockEmbedder
from financial_rag.ingestion.models import Document
from financial_rag.retrieval.models import RetrievalResult
from financial_rag.retrieval.retriever import VectorRetriever
from financial_rag.retrieval.vector_store import FAISSVectorStore


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_chunk(content: str, source: str = "test.pdf", page: int = 0) -> Chunk:
    doc = Document(content=content, source=source, page=page)
    return Chunk.from_document(doc, content, chunk_index=0, total_chunks=1)


def make_retriever(
    texts_with_sources: list[tuple[str, str]],
    dim: int = 16,
    score_threshold: float = 0.0,
) -> VectorRetriever:
    embedder = MockEmbedder(dim=dim)
    store = FAISSVectorStore(dimension=dim)
    chunks = [make_chunk(text, source=source) for text, source in texts_with_sources]
    store.add_chunks(chunks, embedder)
    return VectorRetriever(store=store, embedder=embedder, score_threshold=score_threshold)


# ── RetrievalResult ───────────────────────────────────────────────────────────

class TestRetrievalResult:
    def test_total_reflects_result_count(self):
        retriever = make_retriever([("alpha", "a.pdf"), ("beta", "b.pdf")])
        result = retriever.retrieve("alpha", top_k=2)
        assert result.total == len(result.results)

    def test_is_empty_false_when_results_exist(self):
        # score_threshold=-1.0 ensures the single chunk is always returned
        # regardless of cosine orientation between stored and query vectors.
        retriever = make_retriever([("texto", "doc.pdf")], score_threshold=-1.0)
        result = retriever.retrieve("texto", top_k=1)
        assert not result.is_empty

    def test_is_empty_true_on_empty_store(self):
        store = FAISSVectorStore(dimension=16)
        embedder = MockEmbedder(dim=16)
        retriever = VectorRetriever(store=store, embedder=embedder)
        result = retriever.retrieve("anything")
        assert result.is_empty

    def test_top_is_none_when_empty(self):
        store = FAISSVectorStore(dimension=16)
        embedder = MockEmbedder(dim=16)
        retriever = VectorRetriever(store=store, embedder=embedder)
        assert retriever.retrieve("query").top is None

    def test_citations_length_matches_total(self):
        retriever = make_retriever([
            ("reporte anual", "interbank.pdf"),
            ("memoria 2025", "scotiabank.pdf"),
        ])
        result = retriever.retrieve("reporte", top_k=2)
        assert len(result.citations) == result.total

    def test_citations_are_non_empty_strings(self):
        retriever = make_retriever([("utilidad neta", "interbank.pdf")])
        result = retriever.retrieve("utilidad", top_k=1)
        assert all(isinstance(c, str) and len(c) > 0 for c in result.citations)


# ── VectorRetriever ───────────────────────────────────────────────────────────

class TestVectorRetriever:
    def test_returns_retrieval_result_type(self):
        retriever = make_retriever([("texto", "doc.pdf")])
        assert isinstance(retriever.retrieve("texto"), RetrievalResult)

    def test_captures_original_query(self):
        retriever = make_retriever([("alpha", "a.pdf")])
        result = retriever.retrieve("mi pregunta financiera")
        assert result.query == "mi pregunta financiera"

    def test_top_k_limits_results(self):
        retriever = make_retriever([(f"chunk {i}", f"doc_{i}.pdf") for i in range(10)])
        result = retriever.retrieve("chunk", top_k=3)
        assert result.total <= 3

    def test_retrieve_empty_store(self):
        store = FAISSVectorStore(dimension=16)
        embedder = MockEmbedder(dim=16)
        retriever = VectorRetriever(store=store, embedder=embedder)
        result = retriever.retrieve("cualquier cosa")
        assert result.is_empty

    def test_source_filter_restricts_to_bank(self):
        # score_threshold=-1.0 so all chunks survive FAISS filtering;
        # we're testing source filtering, not relevance scoring.
        retriever = make_retriever([
            ("utilidad neta interbank", "interbank_memoria_2025.pdf"),
            ("riesgo crédito scotiabank", "scotiabank_peru_memoria_2025.pdf"),
            ("dividendos interbank", "interbank_memoria_2025.pdf"),
        ], score_threshold=-1.0)
        result = retriever.retrieve("utilidad", top_k=5, source_filter="scotiabank")
        assert result.total >= 1
        for r in result.results:
            assert "scotiabank" in r.chunk.source.lower()

    def test_source_filter_no_match_returns_empty(self):
        retriever = make_retriever([("reporte interbank", "interbank_memoria_2025.pdf")])
        result = retriever.retrieve("reporte", top_k=5, source_filter="bbva")
        assert result.is_empty

    def test_source_filter_is_case_insensitive(self):
        # score_threshold=-1.0 so the single chunk always passes the score filter;
        # this test is about case-insensitive source filtering, not relevance.
        retriever = make_retriever([("dato", "Interbank_Memoria_2025.pdf")], score_threshold=-1.0)
        result = retriever.retrieve("dato", top_k=5, source_filter="interbank")
        assert result.total == 1

    def test_ranks_are_sequential_after_filter(self):
        retriever = make_retriever([
            ("interbank dato uno", "interbank.pdf"),
            ("scotiabank dato", "scotiabank.pdf"),
            ("interbank dato dos", "interbank.pdf"),
            ("interbank dato tres", "interbank.pdf"),
        ])
        result = retriever.retrieve("dato", top_k=5, source_filter="interbank")
        ranks = [r.rank for r in result.results]
        assert ranks == list(range(result.total))

    def test_score_threshold_filters_low_scores(self):
        data = [("texto alpha", "a.pdf"), ("texto beta", "b.pdf")]
        retriever_loose = make_retriever(data, score_threshold=0.0)
        retriever_strict = make_retriever(data, score_threshold=0.99)
        loose = retriever_loose.retrieve("texto", top_k=5)
        strict = retriever_strict.retrieve("texto", top_k=5)
        assert strict.total <= loose.total

    def test_exact_match_is_top_result(self):
        query = "utilidad neta consolidada interbank 2025"
        retriever = make_retriever([
            (query, "exact.pdf"),
            ("política de dividendos", "other1.pdf"),
            ("gestión riesgos operativos", "other2.pdf"),
        ], dim=32)
        # Match the prepended string added by Chunk.from_document
        embedded_query = f"Document: exact.pdf\n{query}"
        result = retriever.retrieve(embedded_query, top_k=3)
        assert result.top is not None
        assert result.top.chunk.source == "exact.pdf"

    def test_store_size_property(self):
        retriever = make_retriever([("a", "a.pdf"), ("b", "b.pdf"), ("c", "c.pdf")])
        assert retriever.store_size == 3

    def test_no_source_filter_returns_all_sources(self):
        retriever = make_retriever([
            ("reporte interbank", "interbank.pdf"),
            ("reporte scotiabank", "scotiabank.pdf"),
        ], score_threshold=-1.0)
        result = retriever.retrieve("reporte", top_k=5)
        sources = {r.chunk.filename for r in result.results}
        assert len(sources) == 2


# ── VectorRetriever with Reranking ────────────────────────────────────────────

class TestVectorRetrieverReranking:
    def test_reranker_not_called_if_none(self):
        retriever = make_retriever([("a", "a.pdf")], score_threshold=-1.0)
        assert retriever._reranker is None
        assert retriever.retrieve("a").total == 1

    def test_reranker_receives_candidate_pool(self):
        from unittest.mock import MagicMock
        from financial_rag.retrieval.reranker import MockReranker
        reranker = MagicMock(spec=MockReranker)
        reranker.rerank.return_value = []
        retriever = make_retriever([(f"chunk {i}", "doc.pdf") for i in range(10)], score_threshold=-1.0)
        retriever._reranker = reranker
        retriever._reranker_candidates = 8

        retriever.retrieve("chunk", top_k=3)
        
        # Should have called reranker.rerank with 8 candidates (since 8 > 3)
        assert reranker.rerank.called
        args, kwargs = reranker.rerank.call_args
        candidates = args[1]
        assert len(candidates) == 8
        assert kwargs["top_k"] == 3

    def test_reranker_respects_top_k_when_candidate_pool_smaller(self):
        from unittest.mock import MagicMock
        from financial_rag.retrieval.reranker import MockReranker
        reranker = MagicMock(spec=MockReranker)
        reranker.rerank.return_value = []
        retriever = make_retriever([(f"chunk {i}", "doc.pdf") for i in range(10)], score_threshold=-1.0)
        retriever._reranker = reranker
        retriever._reranker_candidates = 2 # smaller than top_k

        retriever.retrieve("chunk", top_k=5)
        
        args, kwargs = reranker.rerank.call_args
        candidates = args[1]
        assert len(candidates) == 5 # max(5, 2)
        assert kwargs["top_k"] == 5

    def test_document_ids_passed_to_store(self):
        from unittest.mock import patch
        retriever = make_retriever([("a", "doc.pdf")])
        with patch.object(retriever._store, 'search', return_value=[]) as mock_search:
            retriever.retrieve("query", document_ids=["doc1"])
            mock_search.assert_called_once()
            assert mock_search.call_args.kwargs["document_ids"] == ["doc1"]

    def test_reranker_preserves_source_filter(self):
        from unittest.mock import MagicMock
        from financial_rag.retrieval.reranker import MockReranker
        reranker = MagicMock(spec=MockReranker)
        reranker.rerank.return_value = []
        retriever = make_retriever([
            ("dato interbank", "interbank.pdf"),
            ("dato bbva", "bbva.pdf"),
        ], score_threshold=-1.0)
        retriever._reranker = reranker

        retriever.retrieve("dato", top_k=2, source_filter="interbank")
        
        args, _ = reranker.rerank.call_args
        candidates = args[1]
        assert len(candidates) == 1
        assert candidates[0].chunk.source == "interbank.pdf"
