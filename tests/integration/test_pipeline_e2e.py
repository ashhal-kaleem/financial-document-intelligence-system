"""End-to-end integration tests.

These tests wire REAL components together — embedding, FAISS, retrieval, pipeline,
and the FastAPI app — without any external LLM API. MockGenerator provides
deterministic answers so no LLM infrastructure is needed.

Unlike unit tests (which isolate one component with mocks), integration tests
verify that the seams between components work correctly.
"""

import pytest
from fastapi.testclient import TestClient

from financial_rag.chunking.models import Chunk
from financial_rag.embeddings.mock import MockEmbedder
from financial_rag.generation.mock import MockGenerator
from financial_rag.generation.models import ConversationTurn, GenerationResult
from financial_rag.pipeline.models import RAGResponse
from financial_rag.pipeline.pipeline import RAGPipeline
from financial_rag.retrieval.hybrid import HybridRetriever
from financial_rag.retrieval.retriever import VectorRetriever
from financial_rag.retrieval.vector_store import FAISSVectorStore


# ── Shared helpers ─────────────────────────────────────────────────────────────

_DIM = 32  # MockEmbedder dimension — small enough to be fast

_CORPUS: list[tuple[str, str]] = [
    ("La utilidad neta de Interbank fue S/ 1,200 millones en 2023.", "interbank_2023.pdf"),
    ("El ROE de Interbank alcanzó 18.5% en el ejercicio 2023.", "interbank_2023.pdf"),
    ("El número de empleados de Interbank ascendió a 8,500 personas.", "interbank_2023.pdf"),
    ("Scotiabank reportó utilidades de S/ 980 millones en 2023.", "scotiabank_2023.pdf"),
    ("El ratio de capital de Scotiabank fue 14.2% al cierre de 2023.", "scotiabank_2023.pdf"),
    ("Scotiabank contaba con 6,200 colaboradores a diciembre 2023.", "scotiabank_2023.pdf"),
]


def _build_chunks(data: list[tuple[str, str]] = _CORPUS) -> list[Chunk]:
    """Create Chunk objects with globally unique chunk_index values."""
    n = len(data)
    return [
        Chunk(
            content=text,
            source=source,
            page=i,
            chunk_index=i,
            total_chunks=n,
            metadata={},
        )
        for i, (text, source) in enumerate(data)
    ]


def _build_store(chunks: list[Chunk], embedder: MockEmbedder) -> FAISSVectorStore:
    store = FAISSVectorStore(dimension=_DIM)
    store.add_chunks(chunks, embedder)
    return store


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def embedder() -> MockEmbedder:
    return MockEmbedder(dim=_DIM)


@pytest.fixture(scope="module")
def chunks() -> list[Chunk]:
    return _build_chunks()


@pytest.fixture(scope="module")
def store(chunks, embedder) -> FAISSVectorStore:
    return _build_store(chunks, embedder)


@pytest.fixture()
def vector_pipeline(store, embedder) -> RAGPipeline:
    retriever = VectorRetriever(store=store, embedder=embedder, score_threshold=-1.0)
    return RAGPipeline(retriever=retriever, generator=MockGenerator(), top_k=3)


@pytest.fixture()
def hybrid_pipeline(store, embedder) -> RAGPipeline:
    retriever = HybridRetriever(store=store, embedder=embedder, score_threshold=-1.0)
    return RAGPipeline(retriever=retriever, generator=MockGenerator(), top_k=3)


@pytest.fixture()
def api_client(vector_pipeline) -> TestClient:
    """FastAPI TestClient with a real pipeline (no external LLM, no disk index)."""
    from financial_rag.api.app import create_app
    app = create_app(store_path="data/processed/vector_store", model="mock")
    app.state.pipeline = vector_pipeline
    with TestClient(app, raise_server_exceptions=True) as client:
        yield client


# ── VectorRetriever pipeline ───────────────────────────────────────────────────

class TestVectorPipeline:
    def test_ask_returns_rag_response(self, vector_pipeline):
        result = vector_pipeline.ask("¿Cuál fue la utilidad neta?")
        assert isinstance(result, RAGResponse)

    def test_ask_is_grounded(self, vector_pipeline):
        result = vector_pipeline.ask("¿Cuál fue la utilidad neta?")
        assert result.is_grounded

    def test_chunks_used_matches_top_k(self, vector_pipeline):
        result = vector_pipeline.ask("utilidad", top_k=2)
        assert result.chunks_used == 2

    def test_latency_fields_are_positive(self, vector_pipeline):
        result = vector_pipeline.ask("pregunta")
        assert result.retrieval_ms > 0
        assert result.generation_ms > 0
        assert result.total_ms == pytest.approx(result.retrieval_ms + result.generation_ms)

    def test_citations_length_matches_chunks_used(self, vector_pipeline):
        result = vector_pipeline.ask("empleados", top_k=2)
        assert len(result.citations) == result.chunks_used

    def test_citations_are_non_empty_strings(self, vector_pipeline):
        result = vector_pipeline.ask("utilidad")
        assert all(isinstance(c, str) and c for c in result.citations)

    def test_source_filter_restricts_to_interbank(self, vector_pipeline):
        result = vector_pipeline.ask("utilidad", top_k=5, source_filter="interbank")
        assert result.is_grounded
        assert all("interbank" in c.lower() for c in result.citations)

    def test_source_filter_restricts_to_scotiabank(self, vector_pipeline):
        result = vector_pipeline.ask("utilidad", top_k=5, source_filter="scotiabank")
        assert result.is_grounded
        assert all("scotiabank" in c.lower() for c in result.citations)

    def test_top_k_limits_retrieved_chunks(self, vector_pipeline):
        r1 = vector_pipeline.ask("pregunta", top_k=1)
        r2 = vector_pipeline.ask("pregunta", top_k=3)
        assert r1.chunks_used == 1
        assert r2.chunks_used == 3

    def test_chunk_texts_populated(self, vector_pipeline):
        result = vector_pipeline.ask("utilidad", top_k=2)
        assert len(result.chunk_texts) == 2
        assert all(isinstance(t, str) and t for t in result.chunk_texts)

    def test_retrieval_scores_length_matches_chunks(self, vector_pipeline):
        result = vector_pipeline.ask("pregunta", top_k=3)
        assert len(result.retrieval_scores) == result.chunks_used

    def test_model_reflects_generator(self, vector_pipeline):
        result = vector_pipeline.ask("pregunta")
        assert result.model == "mock"

    def test_empty_store_is_ungrounded(self, embedder):
        empty_store = FAISSVectorStore(dimension=_DIM)
        retriever = VectorRetriever(store=empty_store, embedder=embedder)
        pipeline = RAGPipeline(retriever=retriever, generator=MockGenerator(), top_k=3)
        result = pipeline.ask("cualquier pregunta")
        assert not result.is_grounded
        assert result.chunks_used == 0


# ── HybridRetriever pipeline ───────────────────────────────────────────────────

class TestHybridPipeline:
    def test_ask_returns_rag_response(self, hybrid_pipeline):
        result = hybrid_pipeline.ask("¿Cuál fue la utilidad neta?")
        assert isinstance(result, RAGResponse)

    def test_ask_is_grounded(self, hybrid_pipeline):
        result = hybrid_pipeline.ask("utilidad neta interbank")
        assert result.is_grounded

    def test_source_filter_applied(self, hybrid_pipeline):
        result = hybrid_pipeline.ask("utilidad", top_k=5, source_filter="scotiabank")
        assert result.is_grounded
        assert all("scotiabank" in c.lower() for c in result.citations)

    def test_returns_at_most_top_k(self, hybrid_pipeline):
        result = hybrid_pipeline.ask("capital ratio", top_k=2)
        assert result.chunks_used <= 2

    def test_bm25_boosts_keyword_match(self, hybrid_pipeline):
        # BM25 contributes to RRF — verify the pipeline runs and returns results.
        # Exact BM25 ranking is validated in tests/unit/test_hybrid_retriever.py.
        result = hybrid_pipeline.ask("scotiabank capital ratio 14.2", top_k=3)
        assert result.is_grounded
        assert result.chunks_used > 0

    def test_latency_fields_positive(self, hybrid_pipeline):
        result = hybrid_pipeline.ask("empleados")
        assert result.retrieval_ms > 0
        assert result.generation_ms > 0


# ── Multi-turn conversation ────────────────────────────────────────────────────

class _HistoryCapture(MockGenerator):
    """MockGenerator that records the history it receives."""
    captured_history: list[ConversationTurn] | None = None

    def generate(
        self,
        retrieval_result,
        history: list[ConversationTurn] | None = None,
        **kwargs,
    ) -> GenerationResult:
        self.captured_history = history
        return super().generate(retrieval_result, history, **kwargs)


class TestMultiturn:
    def test_history_forwarded_to_generator(self, store, embedder):
        generator = _HistoryCapture()
        retriever = VectorRetriever(store=store, embedder=embedder, score_threshold=-1.0)
        pipeline = RAGPipeline(retriever=retriever, generator=generator, top_k=2)

        history = [
            ConversationTurn(role="user", content="¿Cuántos empleados tiene Interbank?"),
            ConversationTurn(role="assistant", content="Interbank tiene 8,500 empleados."),
        ]
        pipeline.ask("¿Y Scotiabank?", history=history)

        assert generator.captured_history is not None
        assert len(generator.captured_history) == 2
        assert generator.captured_history[0].role == "user"
        assert generator.captured_history[1].role == "assistant"

    def test_no_history_passes_none_to_generator(self, store, embedder):
        generator = _HistoryCapture()
        retriever = VectorRetriever(store=store, embedder=embedder, score_threshold=-1.0)
        pipeline = RAGPipeline(retriever=retriever, generator=generator, top_k=2)
        pipeline.ask("pregunta sin historia")
        assert generator.captured_history is None

    def test_empty_history_treated_as_no_history(self, store, embedder):
        generator = _HistoryCapture()
        retriever = VectorRetriever(store=store, embedder=embedder, score_threshold=-1.0)
        pipeline = RAGPipeline(retriever=retriever, generator=generator, top_k=2)
        pipeline.ask("pregunta", history=[])
        # Empty list collapses to None inside RAGPipeline.ask (history=history or None)
        assert not generator.captured_history


# ── FastAPI integration ────────────────────────────────────────────────────────

class TestAPIIntegration:
    def test_ask_returns_200(self, api_client):
        r = api_client.post("/ask", json={"question": "¿Cuál fue la utilidad neta?"})
        assert r.status_code == 200

    def test_ask_response_is_grounded(self, api_client):
        r = api_client.post("/ask", json={"question": "utilidad neta"})
        assert r.json()["is_grounded"] is True

    def test_ask_citations_populated(self, api_client):
        r = api_client.post("/ask", json={"question": "utilidad"})
        assert isinstance(r.json()["citations"], list)
        assert len(r.json()["citations"]) > 0

    def test_ask_total_ms_equals_sum(self, api_client):
        r = api_client.post("/ask", json={"question": "ROE interbank"})
        data = r.json()
        assert data["total_ms"] == pytest.approx(data["retrieval_ms"] + data["generation_ms"])

    def test_ask_source_filter_accepted(self, api_client):
        r = api_client.post(
            "/ask", json={"question": "utilidad", "source_filter": "scotiabank"}
        )
        assert r.status_code == 200
        data = r.json()
        assert data["is_grounded"]
        assert all("scotiabank" in c.lower() for c in data["citations"])

    def test_ask_top_k_override_accepted(self, api_client):
        r = api_client.post("/ask", json={"question": "utilidad", "top_k": 2})
        assert r.status_code == 200
        assert r.json()["chunks_used"] <= 2

    def test_health_store_chunks_reflects_real_store(self, api_client):
        r = api_client.get("/health")
        assert r.status_code == 200
        assert r.json()["store_chunks"] == len(_CORPUS)

    def test_stream_endpoint_returns_200(self, api_client):
        r = api_client.post("/ask/stream", json={"question": "utilidad neta"})
        assert r.status_code == 200

    def test_stream_content_type_is_event_stream(self, api_client):
        r = api_client.post("/ask/stream", json={"question": "utilidad neta"})
        assert "text/event-stream" in r.headers["content-type"]

    def test_stream_contains_done_event(self, api_client):
        r = api_client.post("/ask/stream", json={"question": "utilidad neta"})
        assert b"done" in r.content
