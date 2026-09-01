"""Unit tests for generation models and MockGenerator."""

import pytest

from financial_rag.chunking.models import Chunk
from financial_rag.embeddings.mock import MockEmbedder
from financial_rag.generation.groq import AVAILABLE_GROQ_MODELS as AVAILABLE_MODELS
from financial_rag.generation.factory import create_generator
from financial_rag.generation.mock import MockGenerator
from financial_rag.generation.models import GenerationResult
from financial_rag.ingestion.models import Document
from financial_rag.retrieval.models import RetrievalResult
from financial_rag.retrieval.vector_store import FAISSVectorStore
from financial_rag.retrieval.retriever import VectorRetriever


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_retrieval_result(
    query: str = "¿Cuál fue la utilidad neta?",
    texts: list[str] | None = None,
) -> RetrievalResult:
    texts = texts or ["La utilidad neta de Interbank fue S/ 1,200 millones.", "El ROE fue 18%."]
    embedder = MockEmbedder(dim=16)
    store = FAISSVectorStore(dimension=16)
    chunks = [
        Chunk.from_document(
            Document(content=t, source=f"interbank.pdf", page=i),
            content=t, chunk_index=i, total_chunks=len(texts),
        )
        for i, t in enumerate(texts)
    ]
    store.add_chunks(chunks, embedder)
    retriever = VectorRetriever(store=store, embedder=embedder, score_threshold=-1.0)
    return retriever.retrieve(query, top_k=len(texts))


def empty_retrieval_result(query: str = "pregunta sin respuesta") -> RetrievalResult:
    return RetrievalResult(query=query, results=[])


# ── GenerationResult ──────────────────────────────────────────────────────────

class TestGenerationResult:
    def test_total_tokens(self):
        result = GenerationResult(
            answer="Respuesta.", query="pregunta", citations=[],
            model="mock", input_tokens=100, output_tokens=50,
        )
        assert result.total_tokens == 150

    def test_total_tokens_defaults_zero(self):
        result = GenerationResult(answer="R", query="Q", citations=[], model="mock")
        assert result.total_tokens == 0

    def test_repr_contains_model(self):
        result = GenerationResult(answer="R", query="Q", citations=["c1"], model="llama-3.1-8b-instant")
        assert "llama-3.1-8b-instant" in repr(result)

    def test_repr_contains_citation_count(self):
        result = GenerationResult(
            answer="R", query="Q", citations=["c1", "c2"], model="mock"
        )
        assert "2" in repr(result)


# ── MockGenerator ─────────────────────────────────────────────────────────────

class TestMockGenerator:
    def test_returns_generation_result(self):
        gen = MockGenerator()
        result = gen.generate(make_retrieval_result())
        assert isinstance(result, GenerationResult)

    def test_captures_query(self):
        gen = MockGenerator()
        rr = make_retrieval_result(query="¿Cuál fue el ROE?")
        result = gen.generate(rr)
        assert result.query == "¿Cuál fue el ROE?"

    def test_captures_citations(self):
        gen = MockGenerator()
        rr = make_retrieval_result()
        result = gen.generate(rr)
        assert result.citations == rr.citations

    def test_custom_answer(self):
        gen = MockGenerator(answer="Respuesta personalizada.")
        result = gen.generate(make_retrieval_result())
        assert result.answer == "Respuesta personalizada."

    def test_model_is_mock(self):
        gen = MockGenerator()
        result = gen.generate(make_retrieval_result())
        assert result.model == "mock"

    def test_empty_retrieval_result(self):
        gen = MockGenerator()
        result = gen.generate(empty_retrieval_result())
        assert result.citations == []
        assert isinstance(result.answer, str)

    def test_token_counts_are_positive(self):
        gen = MockGenerator()
        result = gen.generate(make_retrieval_result())
        assert result.input_tokens >= 0
        assert result.output_tokens >= 0

    def test_total_tokens_consistent(self):
        gen = MockGenerator()
        result = gen.generate(make_retrieval_result())
        assert result.total_tokens == result.input_tokens + result.output_tokens


# ── Factory ───────────────────────────────────────────────────────────────────

class TestFactory:
    def test_create_generator_returns_groq_generator(self):
        from unittest.mock import MagicMock, patch
        from financial_rag.generation.groq import GroqGenerator
        with patch("financial_rag.generation.groq._groq_lib") as mock_lib:
            mock_lib.Groq.return_value = MagicMock()
            gen = create_generator(model="llama-3.1-8b-instant", backend="groq")
        assert isinstance(gen, GroqGenerator)

    def test_create_generator_unknown_model_raises(self):
        with pytest.raises(ValueError, match="Unknown model"):
            create_generator(model="gpt-99:fake", backend="groq")

    def test_all_known_models_accepted(self):
        from unittest.mock import MagicMock, patch
        for model in AVAILABLE_MODELS:
            with patch("financial_rag.generation.groq._groq_lib") as mock_lib:
                mock_lib.Groq.return_value = MagicMock()
                gen = create_generator(model=model, backend="groq")
            assert gen is not None

    def test_create_generator_mock_backend(self):
        gen = create_generator(backend="mock")
        assert isinstance(gen, MockGenerator)

    def test_create_generator_unknown_backend_raises(self):
        with pytest.raises(ValueError, match="Unknown backend"):
            create_generator(model="llama-3.1-8b-instant", backend="openai")

    def test_create_generator_unknown_groq_model_raises(self):
        with pytest.raises(ValueError, match="Unknown model"):
            create_generator(model="gpt-4o", backend="groq")


# ── GroqGenerator ─────────────────────────────────────────────────────────────

class TestGroqGenerator:
    def _make_generator(self, answer: str = "Respuesta de prueba."):
        from unittest.mock import MagicMock
        from financial_rag.generation.groq import GroqGenerator

        mock_client = MagicMock()

        # generate() path — non-streaming
        mock_message = MagicMock()
        mock_message.content = answer
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50

        # stream() path — streaming chunks
        stream_chunk = MagicMock()
        stream_chunk.choices = [MagicMock()]
        stream_chunk.choices[0].delta.content = answer

        def create_side_effect(*args, **kwargs):
            if kwargs.get("stream"):
                return iter([stream_chunk])
            return mock_response

        mock_client.chat.completions.create.side_effect = create_side_effect

        return GroqGenerator(_client=mock_client)

    def test_returns_generation_result(self):
        gen = self._make_generator()
        result = gen.generate(make_retrieval_result())
        assert isinstance(result, GenerationResult)

    def test_answer_populated(self):
        gen = self._make_generator(answer="Utilidad neta fue S/ 1,200 millones.")
        result = gen.generate(make_retrieval_result())
        assert result.answer == "Utilidad neta fue S/ 1,200 millones."

    def test_query_captured(self):
        gen = self._make_generator()
        rr = make_retrieval_result(query="¿Cuál fue el ROE?")
        result = gen.generate(rr)
        assert result.query == "¿Cuál fue el ROE?"

    def test_citations_captured(self):
        gen = self._make_generator()
        rr = make_retrieval_result()
        result = gen.generate(rr)
        assert result.citations == rr.citations

    def test_token_counts(self):
        gen = self._make_generator()
        result = gen.generate(make_retrieval_result())
        assert result.input_tokens == 100
        assert result.output_tokens == 50
        assert result.total_tokens == 150

    def test_empty_retrieval_returns_no_context_answer(self):
        from financial_rag.generation.groq import _NO_CONTEXT_ANSWER
        gen = self._make_generator()
        result = gen.generate(empty_retrieval_result())
        assert result.answer == _NO_CONTEXT_ANSWER
        assert result.citations == []

    def test_empty_retrieval_skips_api_call(self):
        from unittest.mock import MagicMock
        from financial_rag.generation.groq import GroqGenerator
        mock_client = MagicMock()
        gen = GroqGenerator(_client=mock_client)
        gen.generate(empty_retrieval_result())
        mock_client.chat.completions.create.assert_not_called()

    def test_stream_yields_tokens(self):
        gen = self._make_generator(answer="token de respuesta")
        tokens = list(gen.stream(make_retrieval_result()))
        assert len(tokens) > 0
        assert "token de respuesta" in "".join(tokens)

    def test_stream_empty_yields_no_context(self):
        from financial_rag.generation.groq import _NO_CONTEXT_ANSWER
        gen = self._make_generator()
        tokens = list(gen.stream(empty_retrieval_result()))
        assert tokens == [_NO_CONTEXT_ANSWER]

    def test_stream_empty_skips_api_call(self):
        from unittest.mock import MagicMock
        from financial_rag.generation.groq import GroqGenerator
        mock_client = MagicMock()
        gen = GroqGenerator(_client=mock_client)
        list(gen.stream(empty_retrieval_result()))
        mock_client.chat.completions.create.assert_not_called()

    def test_repr_contains_class_and_model(self):
        gen = self._make_generator()
        r = repr(gen)
        assert "GroqGenerator" in r
