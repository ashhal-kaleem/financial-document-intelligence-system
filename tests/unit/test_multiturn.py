"""Unit tests for multi-turn conversation support."""

import pytest
from fastapi.testclient import TestClient

from financial_rag.api.app import create_app
from financial_rag.generation.models import ConversationTurn
from financial_rag.generation.mock import MockGenerator
from financial_rag.pipeline.models import RAGResponse


# ── ConversationTurn ──────────────────────────────────────────────────────────

class TestConversationTurn:
    def test_fields(self):
        turn = ConversationTurn(role="user", content="¿Cuál fue la utilidad?")
        assert turn.role == "user"
        assert turn.content == "¿Cuál fue la utilidad?"

    def test_assistant_role(self):
        turn = ConversationTurn(role="assistant", content="La utilidad fue S/ 1,234M.")
        assert turn.role == "assistant"


# ── MockGenerator ignores history ─────────────────────────────────────────────

class TestMockGeneratorHistory:
    def test_accepts_history_kwarg(self):
        from financial_rag.retrieval.models import RetrievalResult
        gen = MockGenerator()
        history = [
            ConversationTurn(role="user", content="pregunta anterior"),
            ConversationTurn(role="assistant", content="respuesta anterior"),
        ]
        result = gen.generate(
            RetrievalResult(query="nueva pregunta", results=[]),
            history=history,
        )
        assert result.answer == gen._answer

    def test_accepts_none_history(self):
        from financial_rag.retrieval.models import RetrievalResult
        gen = MockGenerator()
        result = gen.generate(RetrievalResult(query="q", results=[]), history=None)
        assert result.model == "mock"


# ── Pipeline passes history to generator ──────────────────────────────────────

class TestPipelineHistory:
    def test_history_forwarded_to_generator(self):
        from unittest.mock import MagicMock
        from financial_rag.pipeline.pipeline import RAGPipeline
        from financial_rag.retrieval.models import RetrievalResult
        from financial_rag.chunking.models import Chunk
        from financial_rag.retrieval.vector_store import SearchResult

        mock_retriever = MagicMock()
        chunk = Chunk(content="a", source="doc.pdf", page=0, chunk_index=0, total_chunks=1)
        mock_retriever.retrieve.return_value = RetrievalResult(query="q", results=[SearchResult(chunk, 1.0, 0)])

        mock_generator = MagicMock()
        mock_generator.generate.return_value = RAGResponse(
            answer="resp", query="q", citations=[], retrieval_scores=[],
            chunks_used=1, model="mock", retrieval_ms=1.0, generation_ms=1.0,
        )

        pipeline = RAGPipeline(retriever=mock_retriever, generator=mock_generator)
        history = [ConversationTurn(role="user", content="pregunta previa")]
        pipeline.ask("nueva pregunta", history=history)

        called_history = mock_generator.generate.call_args[1]["history"]
        assert called_history == history

    def test_no_history_passes_none(self):
        from unittest.mock import MagicMock
        from financial_rag.pipeline.pipeline import RAGPipeline
        from financial_rag.retrieval.models import RetrievalResult
        from financial_rag.chunking.models import Chunk
        from financial_rag.retrieval.vector_store import SearchResult

        mock_retriever = MagicMock()
        chunk = Chunk(content="a", source="doc.pdf", page=0, chunk_index=0, total_chunks=1)
        mock_retriever.retrieve.return_value = RetrievalResult(query="q", results=[SearchResult(chunk, 1.0, 0)])

        mock_generator = MagicMock()
        mock_generator.generate.return_value = RAGResponse(
            answer="resp", query="q", citations=[], retrieval_scores=[],
            chunks_used=1, model="mock", retrieval_ms=1.0, generation_ms=1.0,
        )

        pipeline = RAGPipeline(retriever=mock_retriever, generator=mock_generator)
        pipeline.ask("pregunta", history=None)

        called_history = mock_generator.generate.call_args[1]["history"]
        assert called_history is None


# ── API accepts history field ─────────────────────────────────────────────────

class _MockPipelineMulti:
    class _MockRetriever:
        store_size = 5

    class _MockGenerator:
        _model = "mock"

    _retriever = _MockRetriever()
    _generator = _MockGenerator()

    def ask(self, question, top_k=5, source_filter=None, history=None, **kwargs):
        return RAGResponse(
            answer=f"Respuesta con {len(history or [])} turnos de historial",
            query=question,
            citations=[],
            retrieval_scores=[],
            chunks_used=0,
            model="mock",
            retrieval_ms=1.0,
            generation_ms=1.0,
        )


@pytest.fixture()
def multi_client():
    app = create_app(store_path="data/processed/vector_store", model="mock")
    app.state.pipeline = _MockPipelineMulti()
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


class TestAPIHistory:
    def test_history_field_accepted(self, multi_client):
        r = multi_client.post("/ask", json={
            "question": "¿Y cómo compara con Scotiabank?",
            "history": [
                {"role": "user", "content": "¿Cuál fue la utilidad de Interbank?"},
                {"role": "assistant", "content": "La utilidad fue S/ 1,234M."},
            ],
        })
        assert r.status_code == 200

    def test_history_forwarded_to_pipeline(self, multi_client):
        r = multi_client.post("/ask", json={
            "question": "pregunta de seguimiento",
            "history": [
                {"role": "user", "content": "primera pregunta"},
                {"role": "assistant", "content": "primera respuesta"},
            ],
        })
        assert "2 turnos" in r.json()["answer"]

    def test_empty_history_accepted(self, multi_client):
        r = multi_client.post("/ask", json={
            "question": "pregunta sin historial",
            "history": [],
        })
        assert r.status_code == 200

    def test_missing_history_defaults_empty(self, multi_client):
        r = multi_client.post("/ask", json={"question": "pregunta válida"})
        assert r.status_code == 200
        assert "0 turnos" in r.json()["answer"]
