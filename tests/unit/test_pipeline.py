"""Unit tests for RAGPipeline and RAGResponse."""

import pytest

from financial_rag.chunking.models import Chunk
from financial_rag.embeddings.mock import MockEmbedder
from financial_rag.generation.mock import MockGenerator
from financial_rag.ingestion.models import Document
from financial_rag.pipeline.models import RAGResponse
from financial_rag.pipeline.pipeline import RAGPipeline
from financial_rag.retrieval.retriever import VectorRetriever
from financial_rag.retrieval.vector_store import FAISSVectorStore


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_chunk(content: str, source: str = "test.pdf", page: int = 0) -> Chunk:
    doc = Document(content=content, source=source, page=page)
    return Chunk.from_document(doc, content, chunk_index=0, total_chunks=1)


def make_pipeline(
    texts_with_sources: list[tuple[str, str]] | None = None,
    answer: str = "Respuesta de prueba.",
    top_k: int = 3,
) -> RAGPipeline:
    texts_with_sources = texts_with_sources or [
        ("La utilidad neta fue S/ 1,200 millones.", "interbank.pdf"),
        ("El ROE fue 18%.", "interbank.pdf"),
        ("El margen neto fue 22%.", "scotiabank.pdf"),
    ]
    embedder = MockEmbedder(dim=16)
    store = FAISSVectorStore(dimension=16)
    chunks = [make_chunk(t, s) for t, s in texts_with_sources]
    store.add_chunks(chunks, embedder)
    retriever = VectorRetriever(store=store, embedder=embedder, score_threshold=-1.0)
    generator = MockGenerator(answer=answer)
    return RAGPipeline(retriever=retriever, generator=generator, top_k=top_k)


# ── RAGResponse ───────────────────────────────────────────────────────────────

class TestRAGResponse:
    def test_total_ms(self):
        r = RAGResponse(
            answer="R", query="Q", citations=[], retrieval_scores=[],
            chunks_used=2, model="mock", retrieval_ms=10.0, generation_ms=90.0,
        )
        assert r.total_ms == pytest.approx(100.0)

    def test_is_grounded_true(self):
        r = RAGResponse(
            answer="R", query="Q", citations=["c1"], retrieval_scores=[0.8],
            chunks_used=1, model="mock", retrieval_ms=5.0, generation_ms=50.0,
        )
        assert r.is_grounded

    def test_is_grounded_false_when_no_chunks(self):
        r = RAGResponse(
            answer="No sé.", query="Q", citations=[], retrieval_scores=[],
            chunks_used=0, model="mock", retrieval_ms=1.0, generation_ms=10.0,
        )
        assert not r.is_grounded

    def test_top_score_returns_first(self):
        r = RAGResponse(
            answer="R", query="Q", citations=[], retrieval_scores=[0.9, 0.7],
            chunks_used=2, model="mock", retrieval_ms=5.0, generation_ms=50.0,
        )
        assert r.top_score == pytest.approx(0.9)

    def test_top_score_none_when_empty(self):
        r = RAGResponse(
            answer="R", query="Q", citations=[], retrieval_scores=[],
            chunks_used=0, model="mock", retrieval_ms=1.0, generation_ms=10.0,
        )
        assert r.top_score is None

    def test_repr_contains_model(self):
        r = RAGResponse(
            answer="R", query="Q", citations=[], retrieval_scores=[],
            chunks_used=0, model="llama-3.1-8b-instant", retrieval_ms=5.0, generation_ms=50.0,
        )
        assert "llama-3.1-8b-instant" in repr(r)


# ── RAGPipeline ───────────────────────────────────────────────────────────────

class TestRAGPipeline:
    def test_ask_returns_rag_response(self):
        pipeline = make_pipeline()
        result = pipeline.ask("¿Cuál fue la utilidad?")
        assert isinstance(result, RAGResponse)

    def test_ask_captures_query(self):
        pipeline = make_pipeline()
        result = pipeline.ask("¿Cuál fue el ROE?")
        assert result.query == "¿Cuál fue el ROE?"

    def test_answer_comes_from_generator(self):
        pipeline = make_pipeline(answer="Mi respuesta específica.")
        result = pipeline.ask("pregunta")
        assert result.answer == "Mi respuesta específica."

    def test_chunks_used_matches_retrieval(self):
        pipeline = make_pipeline(top_k=2)
        result = pipeline.ask("utilidad")
        assert result.chunks_used <= 2

    def test_retrieval_scores_length_matches_chunks(self):
        pipeline = make_pipeline(top_k=3)
        result = pipeline.ask("utilidad")
        assert len(result.retrieval_scores) == result.chunks_used

    def test_latency_fields_are_positive(self):
        pipeline = make_pipeline()
        result = pipeline.ask("pregunta")
        assert result.retrieval_ms >= 0
        assert result.generation_ms >= 0
        assert result.total_ms >= 0

    def test_total_ms_equals_sum(self):
        pipeline = make_pipeline()
        result = pipeline.ask("pregunta")
        assert result.total_ms == pytest.approx(result.retrieval_ms + result.generation_ms)

    def test_source_filter_restricts_chunks(self):
        pipeline = make_pipeline()
        result = pipeline.ask("margen", source_filter="scotiabank")
        for citation in result.citations:
            assert "scotiabank" in citation.lower()

    def test_top_k_override_in_ask(self):
        pipeline = make_pipeline(top_k=5)
        result = pipeline.ask("utilidad", top_k=1)
        assert result.chunks_used <= 1

    def test_empty_store_returns_ungrounded_response(self):
        embedder = MockEmbedder(dim=16)
        store = FAISSVectorStore(dimension=16)
        retriever = VectorRetriever(store=store, embedder=embedder)
        generator = MockGenerator()
        pipeline = RAGPipeline(retriever=retriever, generator=generator)
        result = pipeline.ask("cualquier pregunta")
        assert not result.is_grounded
        assert result.chunks_used == 0

    def test_model_field_reflects_generator(self):
        pipeline = make_pipeline()
        result = pipeline.ask("pregunta")
        assert result.model == "mock"

    def test_repr_contains_retriever_and_generator(self):
        pipeline = make_pipeline()
        r = repr(pipeline)
        assert "VectorRetriever" in r
        assert "MockGenerator" in r

    def test_evidence_gate_bypassed_for_mock_generator(self):
        # MockGenerator doesn't have _client, so gate is bypassed
        pipeline = make_pipeline()
        result = pipeline.ask("pregunta")
        assert result.is_grounded
        assert result.answer == "Mi respuesta específica."

    def test_evidence_gate_raises_api_error(self):
        # Create a generator with a fake _client that raises an API error
        import groq
        pipeline = make_pipeline()
        pipeline._generator._client = type("MockClient", (), {
            "chat": type("Chat", (), {
                "completions": type("Completions", (), {
                    "create": lambda **kwargs: (_ for _ in ()).throw(groq.RateLimitError("Rate limit exceeded", response=None, body=None))
                })()
            })()
        })()
        
        # When max_score is between 0.3 and 0.65, it triggers the gate
        for r in pipeline._retriever._store.chunks:
            # We can't directly set score here, we just mock the retrieve result
            pass
            
        # Override retrieve to force gate evaluation
        original_retrieve = pipeline._retriever.retrieve
        def mock_retrieve(*args, **kwargs):
            res = original_retrieve(*args, **kwargs)
            for r in res.results:
                r.score = 0.5  # Force gate to run
            return res
        pipeline._retriever.retrieve = mock_retrieve

        with pytest.raises(groq.RateLimitError):
            pipeline.ask("pregunta")

