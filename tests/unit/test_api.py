"""Unit tests for the FastAPI endpoints using a mocked pipeline."""

import pytest
from fastapi.testclient import TestClient

from financial_rag.api.app import create_app
from financial_rag.generation.groq import AVAILABLE_GROQ_MODELS as AVAILABLE_MODELS
from financial_rag.pipeline.models import RAGResponse


# ── Mock pipeline ─────────────────────────────────────────────────────────────

class _MockRetriever:
    store_size = 1421


class _MockGeneratorStub:
    _model = "mock"


class _MockPipeline:
    _retriever = _MockRetriever()
    _generator = _MockGeneratorStub()

    def ask(self, question: str, top_k: int = 5, source_filter=None, document_ids=None, history=None, model=None) -> RAGResponse:
        return RAGResponse(
            answer=f"Respuesta para: {question}",
            query=question,
            citations=["interbank.pdf, p.1 (chunk 1/3)"],
            retrieval_scores=[0.85],
            chunks_used=1,
            model="mock",
            retrieval_ms=12.0,
            generation_ms=88.0,
        )


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def client():
    """TestClient with a pre-injected mock pipeline (no external LLM, no FAISS)."""
    app = create_app(store_path="data/processed/vector_store", model="mock")
    app.state.pipeline = _MockPipeline()
    # Skip lifespan by using the app directly
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


# ── POST /ask ─────────────────────────────────────────────────────────────────

class TestAskEndpoint:
    def test_returns_200(self, client):
        r = client.post("/ask", json={"question": "¿Cuál fue la utilidad neta?"})
        assert r.status_code == 200

    def test_response_contains_answer(self, client):
        r = client.post("/ask", json={"question": "¿Cuál fue la utilidad neta?"})
        assert "answer" in r.json()
        assert len(r.json()["answer"]) > 0

    def test_response_contains_citations(self, client):
        r = client.post("/ask", json={"question": "¿Cuál fue el ROE?"})
        assert "citations" in r.json()
        assert isinstance(r.json()["citations"], list)

    def test_response_contains_latency_fields(self, client):
        r = client.post("/ask", json={"question": "pregunta"})
        data = r.json()
        assert "retrieval_ms" in data
        assert "generation_ms" in data
        assert "total_ms" in data

    def test_total_ms_equals_sum(self, client):
        r = client.post("/ask", json={"question": "pregunta"})
        data = r.json()
        assert data["total_ms"] == pytest.approx(data["retrieval_ms"] + data["generation_ms"])

    def test_is_grounded_field_present(self, client):
        r = client.post("/ask", json={"question": "pregunta"})
        assert "is_grounded" in r.json()

    def test_with_source_filter(self, client):
        r = client.post("/ask", json={"question": "pregunta", "source_filter": "interbank"})
        assert r.status_code == 200

    def test_with_top_k_override(self, client):
        r = client.post("/ask", json={"question": "pregunta", "top_k": 3})
        assert r.status_code == 200

    def test_short_question_returns_422(self, client):
        r = client.post("/ask", json={"question": "ab"})
        assert r.status_code == 422

    def test_missing_question_returns_422(self, client):
        r = client.post("/ask", json={})
        assert r.status_code == 422

    def test_top_k_above_max_returns_422(self, client):
        r = client.post("/ask", json={"question": "pregunta válida", "top_k": 99})
        assert r.status_code == 422


# ── GET /health ───────────────────────────────────────────────────────────────

class TestHealthEndpoint:
    def test_returns_200(self, client):
        r = client.get("/health")
        assert r.status_code == 200

    def test_status_is_ok(self, client):
        r = client.get("/health")
        assert r.json()["status"] == "ok"

    def test_store_chunks_is_integer(self, client):
        r = client.get("/health")
        assert isinstance(r.json()["store_chunks"], int)

    def test_store_chunks_matches_mock(self, client):
        r = client.get("/health")
        assert r.json()["store_chunks"] == 1421


# ── GET /models ───────────────────────────────────────────────────────────────

class TestModelsEndpoint:
    def test_returns_200(self, client):
        r = client.get("/models")
        assert r.status_code == 200

    def test_available_is_list(self, client):
        r = client.get("/models")
        assert isinstance(r.json()["available"], list)

    def test_available_matches_known_models(self, client):
        r = client.get("/models")
        assert r.json()["available"] == AVAILABLE_MODELS

    def test_current_model_present(self, client):
        r = client.get("/models")
        assert "current" in r.json()


# ── POST /ask — model override field ─────────────────────────────────────────

class TestAskModelField:
    def test_model_field_accepted(self, client):
        r = client.post("/ask", json={"question": "pregunta válida", "model": "llama-3.3-70b-versatile"})
        assert r.status_code == 200

    def test_model_field_optional(self, client):
        r = client.post("/ask", json={"question": "pregunta válida"})
        assert r.status_code == 200

    def test_model_field_null_accepted(self, client):
        r = client.post("/ask", json={"question": "pregunta válida", "model": None})
        assert r.status_code == 200


# ── POST /ask/stream ──────────────────────────────────────────────────────────

class _MockRetrieverStream:
    store_size = 1421

    def retrieve(self, question, top_k=5, source_filter=None):
        from financial_rag.retrieval.base import RetrievalResult
        result = RetrievalResult(results=[], query=question)
        return result


class _MockGeneratorStream:
    _model = "mock-stream"
    _think = False

    def stream(self, retrieval_result, history=None, model=None):
        yield "token de prueba"


class _MockPipelineStream:
    _retriever = _MockRetrieverStream()
    _generator = _MockGeneratorStream()

    def ask(self, question, top_k=5, source_filter=None, document_ids=None, history=None):
        from financial_rag.pipeline.models import RAGResponse
        return RAGResponse(
            answer="respuesta stream",
            query=question,
            citations=[],
            retrieval_scores=[],
            chunks_used=0,
            model="mock-stream",
            retrieval_ms=5.0,
            generation_ms=20.0,
        )


@pytest.fixture()
def stream_client():
    app = create_app(store_path="data/processed/vector_store", model="mock")
    app.state.pipeline = _MockPipelineStream()
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


class TestStreamEndpoint:
    def test_returns_200(self, stream_client):
        r = stream_client.post("/ask/stream", json={"question": "pregunta válida"})
        assert r.status_code == 200

    def test_content_type_is_event_stream(self, stream_client):
        r = stream_client.post("/ask/stream", json={"question": "pregunta válida"})
        assert "text/event-stream" in r.headers["content-type"]

    def test_response_contains_done_event(self, stream_client):
        r = stream_client.post("/ask/stream", json={"question": "pregunta válida"})
        assert b"done" in r.content

    def test_model_field_forwarded(self, stream_client):
        r = stream_client.post(
            "/ask/stream", json={"question": "pregunta válida", "model": "llama-3.3-70b-versatile"}
        )
        assert r.status_code == 200

    def test_short_question_returns_422(self, stream_client):
        r = stream_client.post("/ask/stream", json={"question": "ab"})
        assert r.status_code == 422
