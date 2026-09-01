"""Unit tests for SupabaseVectorStore.

All Supabase network calls are mocked — no live Supabase project required.
The mock mirrors the supabase-py builder pattern:
    client.table(name).insert(rows).execute()        -> insert
    client.table(name).select(cols, count=).execute()-> count query
    client.rpc(fn, params).execute()                 -> similarity search
"""

from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock, patch, call
import numpy as np
import pytest

from financial_rag.ingestion.models import Document
from financial_rag.chunking.models import Chunk
from financial_rag.embeddings.mock import MockEmbedder
from financial_rag.retrieval.vector_store import SearchResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_chunk(
    content: str,
    source: str = "report.pdf",
    page: int = 0,
    chunk_index: int = 0,
    total_chunks: int = 1,
) -> Chunk:
    doc = Document(content=content, source=source, page=page)
    return Chunk.from_document(doc, content, chunk_index=chunk_index, total_chunks=total_chunks)


def _fake_supabase_module() -> ModuleType:
    """Return a minimal fake `supabase` module so the import inside __init__ works."""
    mod = ModuleType("supabase")

    def create_client(url: str, key: str) -> MagicMock:  # noqa: ANN001
        return MagicMock()

    mod.create_client = create_client  # type: ignore[attr-defined]
    mod.Client = MagicMock          # type: ignore[attr-defined]
    return mod


# ---------------------------------------------------------------------------
# Fixture: SupabaseVectorStore with fully mocked client
# ---------------------------------------------------------------------------

@pytest.fixture()
def mock_client() -> MagicMock:
    """A MagicMock that replaces the real supabase.Client."""
    return MagicMock()


@pytest.fixture()
def store(mock_client: MagicMock):
    """SupabaseVectorStore whose internal client is replaced by mock_client."""
    fake_supabase = _fake_supabase_module()
    fake_supabase.create_client = MagicMock(return_value=mock_client)

    with patch.dict(sys.modules, {"supabase": fake_supabase}):
        from financial_rag.retrieval.supabase_vector_store import SupabaseVectorStore
        s = SupabaseVectorStore(
            supabase_url="https://example.supabase.co",
            supabase_key="service-key",
        )
    # Replace the client that was set in __init__ with our controllable mock.
    s._client = mock_client
    return s

# ---------------------------------------------------------------------------
# Import helper — re-import after fixture injects the mock module
# ---------------------------------------------------------------------------

def _get_store_class():
    """Import SupabaseVectorStore freshly (supabase module must already be mocked)."""
    from financial_rag.retrieval.supabase_vector_store import SupabaseVectorStore
    return SupabaseVectorStore


# ---------------------------------------------------------------------------
# Tests: add_chunks
# ---------------------------------------------------------------------------

class TestAddChunks:

    def test_add_chunks_calls_insert(self, store, mock_client):
        """add_chunks must call table().insert().execute() once."""
        embedder = MockEmbedder(dim=16)
        chunks = [make_chunk("revenue grew 10%"), make_chunk("net income stable")]

        # Arrange mock chain
        mock_insert_resp = MagicMock()
        mock_client.table.return_value.insert.return_value.execute.return_value = mock_insert_resp

        store.add_chunks(chunks, embedder)

        mock_client.table.assert_called_once_with("chunks")
        insert_call_args = mock_client.table.return_value.insert.call_args
        rows = insert_call_args[0][0]  # first positional arg is the list
        assert len(rows) == 2
        assert rows[0]["content"] == "Document: report.pdf\nrevenue grew 10%"
        assert rows[1]["content"] == "Document: report.pdf\nnet income stable"
        # Embeddings must be plain Python lists (JSON-serialisable)
        assert isinstance(rows[0]["embedding"], list)
        assert len(rows[0]["embedding"]) == 16

    def test_add_chunks_preserves_provenance_fields(self, store, mock_client):
        """Each row must contain source, page, chunk_index, total_chunks, metadata."""
        embedder = MockEmbedder(dim=16)
        chunk = make_chunk(
            "dividends declared",
            source="interbank_2024.pdf",
            page=3,
            chunk_index=1,
            total_chunks=5,
        )
        mock_client.table.return_value.insert.return_value.execute.return_value = MagicMock()

        store.add_chunks([chunk], embedder)

        rows = mock_client.table.return_value.insert.call_args[0][0]
        row = rows[0]
        assert row["source"] == "interbank_2024.pdf"
        assert row["page"] == 3
        assert row["chunk_index"] == 1
        assert row["total_chunks"] == 5
        assert isinstance(row["metadata"], dict)

    def test_add_empty_list_does_nothing(self, store, mock_client):
        """add_chunks([]) must not touch the client at all."""
        embedder = MockEmbedder(dim=16)
        store.add_chunks([], embedder)
        mock_client.table.assert_not_called()

    def test_add_chunks_invalidates_size_cache(self, store, mock_client):
        """After add_chunks the size cache is cleared so next .size re-queries."""
        store._size_cache = 99  # pre-warm stale cache
        embedder = MockEmbedder(dim=16)
        mock_client.table.return_value.insert.return_value.execute.return_value = MagicMock()
        store.add_chunks([make_chunk("text")], embedder)
        assert store._size_cache is None

# ---------------------------------------------------------------------------
# Tests: delete_by_document_id
# ---------------------------------------------------------------------------

class TestDeleteByDocumentId:

    def test_delete_by_document_id_uses_jsonb_filter(self, store, mock_client):
        """Must use metadata->>document_id filter to find chunks."""
        mock_client.table.return_value.delete.return_value.eq.return_value.execute.return_value = MagicMock()
        
        store.delete_by_document_id("test-1234")
        
        mock_client.table.assert_called_once_with("chunks")
        mock_client.table.return_value.delete.assert_called_once()
        mock_client.table.return_value.delete.return_value.eq.assert_called_once_with("metadata->>document_id", "test-1234")

    def test_delete_by_document_id_invalidates_size_cache(self, store, mock_client):
        """After deleting chunks, size cache must be cleared."""
        store._size_cache = 100
        store.delete_by_document_id("test-1234")
        assert store._size_cache is None


# ---------------------------------------------------------------------------
# Tests: search
# ---------------------------------------------------------------------------

class TestSearch:

    def _make_rpc_row(
        self,
        content: str = "net profit",
        source: str = "doc.pdf",
        page: int = 0,
        chunk_index: int = 0,
        total_chunks: int = 1,
        similarity: float = 0.85,
    ) -> dict:
        return {
            "content": content,
            "source": source,
            "page": page,
            "chunk_index": chunk_index,
            "total_chunks": total_chunks,
            "metadata": {},
            "similarity": similarity,
        }

    def _setup_rpc(self, mock_client, rows: list[dict]):
        mock_client.rpc.return_value.execute.return_value = MagicMock(data=rows)

    def test_search_returns_search_results(self, store, mock_client):
        rows = [self._make_rpc_row("revenue up"), self._make_rpc_row("cost down", similarity=0.7)]
        self._setup_rpc(mock_client, rows)

        results = store.search("financial performance", MockEmbedder(dim=16), top_k=2)

        assert len(results) == 2
        assert all(isinstance(r, SearchResult) for r in results)

    def test_search_calls_rpc_with_correct_params(self, store, mock_client):
        self._setup_rpc(mock_client, [])
        embedder = MockEmbedder(dim=16)

        store.search("query text", embedder, top_k=3, score_threshold=0.4)

        mock_client.rpc.assert_called_once_with(
            "match_chunks",
            {
                "query_embedding": embedder.embed_query("query text").tolist(),
                "match_threshold": 0.4,
                "match_count": 3,
                "p_document_ids": None,
            },
        )

    def test_search_result_ranks_are_sequential(self, store, mock_client):
        rows = [
            self._make_rpc_row("first",  similarity=0.9),
            self._make_rpc_row("second", similarity=0.8),
            self._make_rpc_row("third",  similarity=0.7),
        ]
        self._setup_rpc(mock_client, rows)

        results = store.search("query", MockEmbedder(dim=16), top_k=3)
        assert [r.rank for r in results] == [0, 1, 2]

    def test_search_reconstructs_chunk_fields(self, store, mock_client):
        row = self._make_rpc_row(
            content="credit risk increased",
            source="scotiabank_2024.pdf",
            page=7,
            chunk_index=2,
            total_chunks=10,
            similarity=0.92,
        )
        self._setup_rpc(mock_client, [row])

        result = store.search("credit risk", MockEmbedder(dim=16), top_k=1)[0]

        assert result.chunk.content == "credit risk increased"
        assert result.chunk.source == "scotiabank_2024.pdf"
        assert result.chunk.page == 7
        assert result.chunk.chunk_index == 2
        assert result.chunk.total_chunks == 10
        assert result.score == pytest.approx(0.92)

    def test_search_empty_rpc_response(self, store, mock_client):
        self._setup_rpc(mock_client, [])
        results = store.search("anything", MockEmbedder(dim=16))
        assert results == []

    def test_search_rpc_none_data_treated_as_empty(self, store, mock_client):
        mock_client.rpc.return_value.execute.return_value = MagicMock(data=None)
        results = store.search("query", MockEmbedder(dim=16))
        assert results == []

    def test_search_result_citation_non_empty(self, store, mock_client):
        self._setup_rpc(mock_client, [self._make_rpc_row(source="report.pdf", page=1)])
        results = store.search("q", MockEmbedder(dim=16), top_k=1)
        assert results[0].citation != ""

# ---------------------------------------------------------------------------
# Tests: size / is_empty / chunks
# ---------------------------------------------------------------------------

class TestSizeAndProperties:

    def test_size_queries_count(self, store, mock_client):
        mock_client.table.return_value.select.return_value.execute.return_value = MagicMock(
            count=42
        )
        assert store.size == 42
        mock_client.table.assert_called_with("chunks")
        mock_client.table.return_value.select.assert_called_with("id", count="exact")

    def test_size_cached_after_first_call(self, store, mock_client):
        mock_client.table.return_value.select.return_value.execute.return_value = MagicMock(
            count=5
        )
        _ = store.size
        _ = store.size  # second call must not hit the client again
        assert mock_client.table.return_value.select.return_value.execute.call_count == 1

    def test_size_none_count_returns_zero(self, store, mock_client):
        mock_client.table.return_value.select.return_value.execute.return_value = MagicMock(
            count=None
        )
        assert store.size == 0

    def test_is_empty_true_when_size_zero(self, store, mock_client):
        mock_client.table.return_value.select.return_value.execute.return_value = MagicMock(
            count=0
        )
        assert store.is_empty is True

    def test_is_empty_false_when_rows_exist(self, store, mock_client):
        mock_client.table.return_value.select.return_value.execute.return_value = MagicMock(
            count=3
        )
        assert store.is_empty is False

    def test_chunks_returns_list_of_chunk(self, store, mock_client):
        rows = [
            {"content": "a", "source": "x.pdf", "page": 0,
             "chunk_index": 0, "total_chunks": 1, "metadata": {}},
            {"content": "b", "source": "y.pdf", "page": 1,
             "chunk_index": 0, "total_chunks": 2, "metadata": {"k": "v"}},
        ]
        mock_client.table.return_value.select.return_value.execute.return_value = MagicMock(
            data=rows
        )
        chunks = store.chunks
        assert len(chunks) == 2
        assert chunks[0].content == "a"
        assert chunks[1].metadata == {"k": "v"}

    def test_chunks_none_data_returns_empty(self, store, mock_client):
        mock_client.table.return_value.select.return_value.execute.return_value = MagicMock(
            data=None
        )
        assert store.chunks == []


# ---------------------------------------------------------------------------
# Tests: repr
# ---------------------------------------------------------------------------

class TestRepr:

    def test_repr_contains_table_name(self, store, mock_client):
        assert "chunks" in repr(store)

    def test_repr_with_warm_cache(self, store, mock_client):
        store._size_cache = 7
        assert "7" in repr(store)


# ---------------------------------------------------------------------------
# Tests: VectorRetriever compatibility
# ---------------------------------------------------------------------------

class TestVectorRetrieverCompatibility:
    """Verify that VectorRetriever accepts SupabaseVectorStore unchanged."""

    def test_vector_retriever_accepts_supabase_store(self, store, mock_client):
        from financial_rag.retrieval.retriever import VectorRetriever

        # Wire up the mock so retrieve() can call store.search()
        mock_client.rpc.return_value.execute.return_value = MagicMock(
            data=[{
                "content": "profit up",
                "source": "bank.pdf",
                "page": 0,
                "chunk_index": 0,
                "total_chunks": 1,
                "metadata": {},
                "similarity": 0.88,
            }]
        )

        embedder = MockEmbedder(dim=16)
        retriever = VectorRetriever(store=store, embedder=embedder, score_threshold=0.0)
        result = retriever.retrieve("profit", top_k=1)

        assert result.total == 1
        assert result.top.score == pytest.approx(0.88)

    def test_store_size_via_retriever(self, store, mock_client):
        from financial_rag.retrieval.retriever import VectorRetriever

        store._size_cache = 10
        retriever = VectorRetriever(store=store, embedder=MockEmbedder(dim=16))
        assert retriever.store_size == 10


# ---------------------------------------------------------------------------
# Tests: import error without supabase package
# ---------------------------------------------------------------------------

class TestImportGuard:

    def test_missing_supabase_raises_import_error(self):
        """If supabase is not installed the store must raise ImportError with a hint."""
        import builtins

        real_import = builtins.__import__

        def _block_supabase(name, *args, **kwargs):
            if name == "supabase" or name.startswith("supabase."):
                raise ImportError(f"Mocked missing package: {name}")
            return real_import(name, *args, **kwargs)

        # Remove the cached store module so its lazy import re-executes
        sys.modules.pop("financial_rag.retrieval.supabase_vector_store", None)
        try:
            builtins.__import__ = _block_supabase
            from financial_rag.retrieval.supabase_vector_store import SupabaseVectorStore
            with pytest.raises(ImportError, match="supabase"):
                SupabaseVectorStore("https://x.supabase.co", "key")
        finally:
            builtins.__import__ = real_import
            sys.modules.pop("financial_rag.retrieval.supabase_vector_store", None)
