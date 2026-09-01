"""Unit tests for retrieval.factory.create_retriever and pipeline.factory.create_pipeline.

All external dependencies (FAISS load, SupabaseVectorStore, GroqGenerator) are
mocked so these tests run fully offline and without disk state.
"""

from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest

from financial_rag.embeddings.mock import MockEmbedder
from financial_rag.pipeline.pipeline import RAGPipeline
from financial_rag.retrieval.retriever import VectorRetriever
from financial_rag.retrieval.vector_store import FAISSVectorStore


# ---------------------------------------------------------------------------
# Shared mock builders
# ---------------------------------------------------------------------------

def _fake_faiss_store(size: int = 0) -> MagicMock:
    """Return a MagicMock that looks like a loaded FAISSVectorStore."""
    store = MagicMock(spec=FAISSVectorStore)
    store.size = size
    store.chunks = []
    return store


def _fake_supabase_module() -> ModuleType:
    mod = ModuleType("supabase")
    mod.create_client = MagicMock(return_value=MagicMock())  # type: ignore[attr-defined]
    mod.Client = MagicMock()                                  # type: ignore[attr-defined]
    return mod


# ---------------------------------------------------------------------------
# Tests: retrieval.factory.create_retriever — FAISS backend
# ---------------------------------------------------------------------------

class TestCreateRetrieverFAISS:

    def test_returns_vector_retriever(self, tmp_path):
        with patch("financial_rag.retrieval.factory.FAISSVectorStore") as MockStore:
            MockStore.load.return_value = _fake_faiss_store()
            from financial_rag.retrieval.factory import create_retriever
            retriever = create_retriever(
                store_path=tmp_path / "idx",
                embedder=MockEmbedder(dim=16),
                backend="faiss",
            )
        assert isinstance(retriever, VectorRetriever)

    def test_faiss_is_default_backend(self, tmp_path):
        with patch("financial_rag.retrieval.factory.FAISSVectorStore") as MockStore:
            MockStore.load.return_value = _fake_faiss_store()
            from financial_rag.retrieval.factory import create_retriever
            retriever = create_retriever(
                store_path=tmp_path / "idx",
                embedder=MockEmbedder(dim=16),
                # no backend= arg
            )
        assert isinstance(retriever, VectorRetriever)

    def test_faiss_load_called_with_store_path(self, tmp_path):
        idx_path = tmp_path / "my_index"
        with patch("financial_rag.retrieval.factory.FAISSVectorStore") as MockStore:
            MockStore.load.return_value = _fake_faiss_store()
            from financial_rag.retrieval.factory import create_retriever
            create_retriever(store_path=idx_path, embedder=MockEmbedder(dim=16))
        MockStore.load.assert_called_once_with(idx_path)

    def test_use_hybrid_returns_hybrid_retriever(self, tmp_path):
        with patch("financial_rag.retrieval.factory.FAISSVectorStore") as MockStore:
            MockStore.load.return_value = _fake_faiss_store()
            with patch("financial_rag.retrieval.factory.HybridRetriever") as MockHybrid:
                MockHybrid.return_value = MagicMock()
                from financial_rag.retrieval.factory import create_retriever
                result = create_retriever(
                    store_path=tmp_path / "idx",
                    embedder=MockEmbedder(dim=16),
                    use_hybrid=True,
                    backend="faiss",
                )
        assert result is MockHybrid.return_value

    def test_score_threshold_forwarded(self, tmp_path):
        with patch("financial_rag.retrieval.factory.FAISSVectorStore") as MockStore:
            MockStore.load.return_value = _fake_faiss_store()
            from financial_rag.retrieval.factory import create_retriever
            retriever = create_retriever(
                store_path=tmp_path / "idx",
                embedder=MockEmbedder(dim=16),
                score_threshold=0.42,
                backend="faiss",
            )
        assert retriever._score_threshold == pytest.approx(0.42)

# ---------------------------------------------------------------------------
# Tests: retrieval.factory.create_retriever — Supabase backend
# ---------------------------------------------------------------------------

class TestCreateRetrieverSupabase:

    @pytest.fixture(autouse=True)
    def _inject_supabase_module(self):
        """Inject fake supabase module before each test, clean up after."""
        fake = _fake_supabase_module()
        sys.modules.pop("supabase", None)
        sys.modules.pop("financial_rag.retrieval.supabase_vector_store", None)
        sys.modules["supabase"] = fake
        yield
        sys.modules.pop("supabase", None)
        sys.modules.pop("financial_rag.retrieval.supabase_vector_store", None)

    def test_returns_vector_retriever(self):
        from financial_rag.retrieval.factory import create_retriever
        retriever = create_retriever(
            embedder=MockEmbedder(dim=16),
            backend="supabase",
            supabase_url="https://x.supabase.co",
            supabase_key="key",
        )
        assert isinstance(retriever, VectorRetriever)

    def test_store_is_supabase_vector_store(self):
        from financial_rag.retrieval.factory import create_retriever
        from financial_rag.retrieval.supabase_vector_store import SupabaseVectorStore
        retriever = create_retriever(
            embedder=MockEmbedder(dim=16),
            backend="supabase",
            supabase_url="https://x.supabase.co",
            supabase_key="key",
        )
        assert isinstance(retriever._store, SupabaseVectorStore)

    def test_supabase_table_forwarded(self):
        from financial_rag.retrieval.factory import create_retriever
        retriever = create_retriever(
            embedder=MockEmbedder(dim=16),
            backend="supabase",
            supabase_url="https://x.supabase.co",
            supabase_key="key",
            supabase_table="my_chunks",
        )
        assert retriever._store._table == "my_chunks"

    def test_supabase_rpc_forwarded(self):
        from financial_rag.retrieval.factory import create_retriever
        retriever = create_retriever(
            embedder=MockEmbedder(dim=16),
            backend="supabase",
            supabase_url="https://x.supabase.co",
            supabase_key="key",
            supabase_rpc="my_match_fn",
        )
        assert retriever._store._rpc_fn == "my_match_fn"

    def test_store_path_ignored_for_supabase(self, tmp_path):
        """FAISSVectorStore.load must NOT be called when backend='supabase'."""
        with patch("financial_rag.retrieval.factory.FAISSVectorStore") as MockFAISS:
            from financial_rag.retrieval.factory import create_retriever
            create_retriever(
                store_path=tmp_path / "idx",
                embedder=MockEmbedder(dim=16),
                backend="supabase",
                supabase_url="https://x.supabase.co",
                supabase_key="key",
            )
        MockFAISS.load.assert_not_called()

    def test_score_threshold_forwarded(self):
        from financial_rag.retrieval.factory import create_retriever
        retriever = create_retriever(
            embedder=MockEmbedder(dim=16),
            backend="supabase",
            supabase_url="https://x.supabase.co",
            supabase_key="key",
            score_threshold=0.55,
        )
        assert retriever._score_threshold == pytest.approx(0.55)

    def test_use_hybrid_with_supabase_raises(self):
        from financial_rag.retrieval.factory import create_retriever
        with pytest.raises(ValueError, match="use_hybrid"):
            create_retriever(
                embedder=MockEmbedder(dim=16),
                backend="supabase",
                supabase_url="https://x.supabase.co",
                supabase_key="key",
                use_hybrid=True,
            )


# ---------------------------------------------------------------------------
# Tests: retrieval.factory.create_retriever — validation
# ---------------------------------------------------------------------------

class TestCreateRetrieverValidation:

    def test_unknown_backend_raises_value_error(self, tmp_path):
        from financial_rag.retrieval.factory import create_retriever
        with pytest.raises(ValueError, match="Unknown backend"):
            create_retriever(
                store_path=tmp_path / "idx",
                embedder=MockEmbedder(dim=16),
                backend="pinecone",
            )

    def test_error_message_lists_valid_options(self, tmp_path):
        from financial_rag.retrieval.factory import create_retriever
        with pytest.raises(ValueError, match="faiss"):
            create_retriever(
                store_path=tmp_path / "idx",
                embedder=MockEmbedder(dim=16),
                backend="invalid",
            )

# ---------------------------------------------------------------------------
# Tests: pipeline.factory.create_pipeline
# ---------------------------------------------------------------------------

class TestCreatePipeline:
    """Test that create_pipeline correctly threads backend args into create_retriever."""

    def _mock_groq(self):
        groq_mock = MagicMock()
        groq_mock.return_value = MagicMock()
        return groq_mock

    def test_returns_rag_pipeline_faiss(self, tmp_path):
        with patch("financial_rag.retrieval.factory.FAISSVectorStore") as MockStore:
            MockStore.load.return_value = _fake_faiss_store()
            with patch("financial_rag.pipeline.factory.GroqGenerator", self._mock_groq()):
                from financial_rag.pipeline.factory import create_pipeline
                pipeline = create_pipeline(
                    store_path=tmp_path / "idx",
                    backend="faiss",
                )
        assert isinstance(pipeline, RAGPipeline)

    def test_faiss_is_default_in_pipeline(self, tmp_path):
        with patch("financial_rag.retrieval.factory.FAISSVectorStore") as MockStore:
            MockStore.load.return_value = _fake_faiss_store()
            with patch("financial_rag.pipeline.factory.GroqGenerator", self._mock_groq()):
                from financial_rag.pipeline.factory import create_pipeline
                pipeline = create_pipeline(store_path=tmp_path / "idx")
        assert isinstance(pipeline, RAGPipeline)

    def test_returns_rag_pipeline_supabase(self):
        fake = _fake_supabase_module()
        sys.modules.pop("supabase", None)
        sys.modules.pop("financial_rag.retrieval.supabase_vector_store", None)
        sys.modules["supabase"] = fake
        try:
            with patch("financial_rag.pipeline.factory.GroqGenerator", self._mock_groq()):
                from financial_rag.pipeline.factory import create_pipeline
                pipeline = create_pipeline(
                    backend="supabase",
                    supabase_url="https://x.supabase.co",
                    supabase_key="key",
                )
            assert isinstance(pipeline, RAGPipeline)
        finally:
            sys.modules.pop("supabase", None)
            sys.modules.pop("financial_rag.retrieval.supabase_vector_store", None)

    def test_supabase_pipeline_uses_supabase_store(self):
        fake = _fake_supabase_module()
        sys.modules.pop("supabase", None)
        sys.modules.pop("financial_rag.retrieval.supabase_vector_store", None)
        sys.modules["supabase"] = fake
        try:
            from financial_rag.retrieval.supabase_vector_store import SupabaseVectorStore
            with patch("financial_rag.pipeline.factory.GroqGenerator", self._mock_groq()):
                from financial_rag.pipeline.factory import create_pipeline
                pipeline = create_pipeline(
                    backend="supabase",
                    supabase_url="https://x.supabase.co",
                    supabase_key="key",
                )
            assert isinstance(pipeline._retriever._store, SupabaseVectorStore)
        finally:
            sys.modules.pop("supabase", None)
            sys.modules.pop("financial_rag.retrieval.supabase_vector_store", None)

    def test_pipeline_top_k_forwarded(self, tmp_path):
        with patch("financial_rag.retrieval.factory.FAISSVectorStore") as MockStore:
            MockStore.load.return_value = _fake_faiss_store()
            with patch("financial_rag.pipeline.factory.GroqGenerator", self._mock_groq()):
                from financial_rag.pipeline.factory import create_pipeline
                pipeline = create_pipeline(
                    store_path=tmp_path / "idx",
                    backend="faiss",
                    top_k=7,
                )
        assert pipeline._top_k == 7

    def test_pipeline_invalid_backend_raises(self, tmp_path):
        with patch("financial_rag.pipeline.factory.GroqGenerator", self._mock_groq()):
            from financial_rag.pipeline.factory import create_pipeline
            with pytest.raises(ValueError, match="Unknown backend"):
                create_pipeline(
                    store_path=tmp_path / "idx",
                    backend="weaviate",
                )

    def test_pipeline_supabase_table_forwarded(self):
        fake = _fake_supabase_module()
        sys.modules.pop("supabase", None)
        sys.modules.pop("financial_rag.retrieval.supabase_vector_store", None)
        sys.modules["supabase"] = fake
        try:
            with patch("financial_rag.pipeline.factory.GroqGenerator", self._mock_groq()):
                from financial_rag.pipeline.factory import create_pipeline
                pipeline = create_pipeline(
                    backend="supabase",
                    supabase_url="https://x.supabase.co",
                    supabase_key="key",
                    supabase_table="custom_chunks",
                )
            assert pipeline._retriever._store._table == "custom_chunks"
        finally:
            sys.modules.pop("supabase", None)
            sys.modules.pop("financial_rag.retrieval.supabase_vector_store", None)


# ---------------------------------------------------------------------------
# Tests: api/app.py — backend selection via create_app
# ---------------------------------------------------------------------------

class TestCreateAppBackend:
    """Verify create_app stores the backend on app.state correctly."""

    def test_default_backend_is_settings_vector_store(self):
        """When no backend kwarg given, settings.vector_store is used."""
        from financial_rag.api.app import create_app
        with patch("financial_rag.api.app.settings") as mock_settings:
            mock_settings.vector_store = "faiss"
            mock_settings.supabase_url = ""
            mock_settings.supabase_key = ""
            mock_settings.supabase_table = "chunks"
            mock_settings.supabase_rpc = "match_chunks"
            mock_settings.cors_origins = "http://localhost:3000"
            app = create_app()
        assert app.state.backend == "faiss"

    def test_explicit_backend_overrides_settings(self):
        from financial_rag.api.app import create_app
        with patch("financial_rag.api.app.settings") as mock_settings:
            mock_settings.vector_store = "faiss"
            mock_settings.supabase_url = "https://x.supabase.co"
            mock_settings.supabase_key = "k"
            mock_settings.supabase_table = "chunks"
            mock_settings.supabase_rpc = "match_chunks"
            mock_settings.cors_origins = "http://localhost:3000"
            app = create_app(backend="supabase")
        assert app.state.backend == "supabase"

    def test_supabase_credentials_stored_on_state(self):
        from financial_rag.api.app import create_app
        with patch("financial_rag.api.app.settings") as mock_settings:
            mock_settings.vector_store = "supabase"
            mock_settings.supabase_url = "https://proj.supabase.co"
            mock_settings.supabase_key = "service-key"
            mock_settings.supabase_table = "chunks"
            mock_settings.supabase_rpc = "match_chunks"
            mock_settings.cors_origins = "http://localhost:3000"
            app = create_app()
        assert app.state.supabase_url == "https://proj.supabase.co"
        assert app.state.supabase_key == "service-key"

    def test_pipeline_initialised_to_none(self):
        from financial_rag.api.app import create_app
        with patch("financial_rag.api.app.settings") as mock_settings:
            mock_settings.vector_store = "faiss"
            mock_settings.supabase_url = ""
            mock_settings.supabase_key = ""
            mock_settings.supabase_table = "chunks"
            mock_settings.supabase_rpc = "match_chunks"
            mock_settings.cors_origins = "http://localhost:3000"
            app = create_app()
        assert app.state.pipeline is None
