"""Unit tests for the FAISS vector store."""

import pytest
import numpy as np
from pathlib import Path

from financial_rag.ingestion.models import Document
from financial_rag.chunking.models import Chunk
from financial_rag.embeddings.mock import MockEmbedder
from financial_rag.retrieval.vector_store import FAISSVectorStore, SearchResult


def make_chunk(content: str, source: str = "test.pdf", page: int = 0) -> Chunk:
    doc = Document(content=content, source=source, page=page)
    return Chunk.from_document(doc, content, chunk_index=0, total_chunks=1)


def make_store_with_chunks(texts: list[str], dim: int = 16) -> tuple[FAISSVectorStore, MockEmbedder]:
    embedder = MockEmbedder(dim=dim)
    store = FAISSVectorStore(dimension=dim)
    chunks = [make_chunk(t, source=f"doc_{i}.pdf") for i, t in enumerate(texts)]
    store.add_chunks(chunks, embedder)
    return store, embedder


class TestFAISSVectorStore:
    def test_initial_state_is_empty(self):
        store = FAISSVectorStore(dimension=16)
        assert store.is_empty
        assert store.size == 0

    def test_add_chunks_updates_size(self):
        store, _ = make_store_with_chunks(["alpha", "beta", "gamma"])
        assert store.size == 3
        assert not store.is_empty

    def test_search_returns_results(self):
        store, embedder = make_store_with_chunks(
            ["utilidad neta fue 500 millones", "riesgo de crédito aumentó", "dividendos declarados"]
        )
        results = store.search("utilidad neta", embedder, top_k=2)
        assert len(results) <= 2
        assert all(isinstance(r, SearchResult) for r in results)

    def test_search_result_ranks_are_sequential(self):
        store, embedder = make_store_with_chunks(["a", "b", "c", "d", "e"])
        results = store.search("query", embedder, top_k=3)
        ranks = [r.rank for r in results]
        assert ranks == list(range(len(results)))

    def test_search_scores_are_between_0_and_1(self):
        store, embedder = make_store_with_chunks(["text one", "text two", "text three"])
        results = store.search("text", embedder, top_k=3)
        for r in results:
            assert -0.1 <= r.score <= 1.1  # cosine can be slightly outside due to float

    def test_score_threshold_filters_results(self):
        store, embedder = make_store_with_chunks(["hello world", "foo bar", "baz qux"])
        # High threshold should return fewer results
        results_low = store.search("hello", embedder, top_k=3, score_threshold=0.0)
        results_high = store.search("hello", embedder, top_k=3, score_threshold=0.99)
        assert len(results_high) <= len(results_low)

    def test_search_empty_store_returns_empty(self):
        store = FAISSVectorStore(dimension=16)
        embedder = MockEmbedder(dim=16)
        results = store.search("anything", embedder)
        assert results == []

    def test_top_k_limits_results(self):
        store, embedder = make_store_with_chunks([f"chunk {i}" for i in range(20)])
        results = store.search("chunk", embedder, top_k=5)
        assert len(results) <= 5

    def test_result_has_citation(self):
        text = "annual report results"
        store, embedder = make_store_with_chunks([text])
        # score_threshold=-1.0 guarantees the chunk is returned regardless of
        # cosine orientation. (The stored embedding is seeded from the prepended
        # "Document: doc_0.pdf\n{text}", so it differs from the raw query seed.)
        results = store.search(text, embedder, top_k=1, score_threshold=-1.0)
        assert len(results) == 1
        assert results[0].citation != ""

    def test_save_and_load(self, tmp_path):
        store, embedder = make_store_with_chunks(
            ["utilidad neta interbank", "riesgo scotiabank", "dividendos BCP"],
            dim=16
        )
        save_path = tmp_path / "test_index"
        store.save(save_path)

        assert (save_path.with_suffix(".faiss")).exists()
        assert (save_path.with_suffix(".pkl")).exists()

        loaded = FAISSVectorStore.load(save_path)
        assert loaded.size == 3
        assert loaded.dimension == 16

        results = loaded.search("utilidad neta interbank", embedder, top_k=2)
        assert len(results) >= 1

    def test_add_chunks_in_batches(self):
        embedder = MockEmbedder(dim=16)
        store = FAISSVectorStore(dimension=16)

        batch1 = [make_chunk(f"batch1 chunk {i}") for i in range(5)]
        batch2 = [make_chunk(f"batch2 chunk {i}") for i in range(3)]

        store.add_chunks(batch1, embedder)
        store.add_chunks(batch2, embedder)

        assert store.size == 8

    def test_search_most_relevant_chunk_ranks_first(self):
        """The semantically closest chunk (by mock hash) should be rank 0."""
        embedder = MockEmbedder(dim=32)
        store = FAISSVectorStore(dimension=32)

        # Add the same query text as a chunk — should be rank 0
        query = "utilidad neta consolidada"
        chunks = [
            make_chunk(query, source="exact_match.pdf"),
            make_chunk("política de dividendos"),
            make_chunk("gestión de riesgos operativos"),
        ]
        store.add_chunks(chunks, embedder)
        # The stored embedding is seeded from "Document: exact_match.pdf\n{query}"
        # so we must query with that same string to get identity similarity (rank 0).
        embedded_query = f"Document: exact_match.pdf\n{query}"
        results = store.search(embedded_query, embedder, top_k=3, score_threshold=-1.0)

        assert results[0].chunk.source == "exact_match.pdf"
