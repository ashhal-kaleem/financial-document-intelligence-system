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
        turn = ConversationTurn(role="user", content="What was the net profit?")
        assert turn.role == "user"
        assert turn.content == "What was the net profit?"

    def test_assistant_role(self):
        turn = ConversationTurn(role="assistant", content="Net profit was S/ 1,234M.")
        assert turn.role == "assistant"


# ── MockGenerator ignores history ─────────────────────────────────────────────

class TestMockGeneratorHistory:
    def test_accepts_history_kwarg(self):
        from financial_rag.retrieval.models import RetrievalResult
        gen = MockGenerator()
        history = [
            ConversationTurn(role="user", content="previous question"),
            ConversationTurn(role="assistant", content="previous answer"),
        ]
        result = gen.generate(
            RetrievalResult(query="new question", results=[]),
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
        history = [ConversationTurn(role="user", content="previous question")]
        pipeline.ask("new question", history=history)

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
        pipeline.ask("question", history=None)

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
            answer=f"Response with {len(history or [])} history turns",
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
            "question": "How does that compare to Scotiabank?",
            "history": [
                {"role": "user", "content": "What was Interbank's net profit?"},
                {"role": "assistant", "content": "Net profit was S/ 1,234M."},
            ],
        })
        assert r.status_code == 200

    def test_history_forwarded_to_pipeline(self, multi_client):
        r = multi_client.post("/ask", json={
            "question": "follow-up question",
            "history": [
                {"role": "user", "content": "first question"},
                {"role": "assistant", "content": "first answer"},
            ],
        })
        assert "2 history turns" in r.json()["answer"]

    def test_empty_history_accepted(self, multi_client):
        r = multi_client.post("/ask", json={
            "question": "question without history",
            "history": [],
        })
        assert r.status_code == 200

    def test_missing_history_defaults_empty(self, multi_client):
        r = multi_client.post("/ask", json={"question": "valid question"})
        assert r.status_code == 200
        assert "0 history turns" in r.json()["answer"]
