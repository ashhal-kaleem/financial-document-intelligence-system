"""Unit tests for the Evidence Gate in RAGPipeline."""
from unittest.mock import Mock, MagicMock
import pytest

from financial_rag.pipeline.pipeline import RAGPipeline
from financial_rag.retrieval.models import RetrievalResult
from financial_rag.retrieval.vector_store import SearchResult
from financial_rag.chunking.models import Chunk
from financial_rag.generation.models import GenerationResult

class MockRetriever:
    def __init__(self, result: RetrievalResult):
        self.result = result
        
    def retrieve(self, question: str, **kwargs):
        self.kwargs = kwargs
        return self.result

class MockGenerator:
    def __init__(self, gate_response: str):
        self.gate_response = gate_response
        self.generate_called = False
        
        # Mock the Groq client used by the gate
        self._client = MagicMock()
        mock_completion = MagicMock()
        mock_completion.choices[0].message.content = gate_response
        self._client.chat.completions.create.return_value = mock_completion
        
    def generate(self, retrieval_result, history=None, model=None):
        self.generate_called = True
        return GenerationResult(
            answer="Generated Answer",
            query=retrieval_result.query,
            citations=["doc1.pdf"],
            model="test-model"
        )

@pytest.fixture
def empty_retriever():
    return MockRetriever(RetrievalResult(query="test", results=[]))

@pytest.fixture
def high_confidence_retriever():
    chunk = Chunk(content="Fact 1", source="doc1.pdf", page=0, chunk_index=0, total_chunks=1)
    res = SearchResult(chunk=chunk, score=0.8, rank=0)
    return MockRetriever(RetrievalResult(query="test", results=[res]))

@pytest.fixture
def low_confidence_retriever():
    chunk = Chunk(content="Fact 1", source="doc1.pdf", page=0, chunk_index=0, total_chunks=1)
    res = SearchResult(chunk=chunk, score=0.2, rank=0)
    return MockRetriever(RetrievalResult(query="test", results=[res]))

@pytest.fixture
def borderline_retriever():
    chunk = Chunk(content="Fact 1", source="doc1.pdf", page=0, chunk_index=0, total_chunks=1)
    res = SearchResult(chunk=chunk, score=0.5, rank=0)
    return MockRetriever(RetrievalResult(query="test", results=[res]))

@pytest.fixture
def multi_doc_retriever():
    c1 = Chunk(content="Fact A", source="doc1.pdf", page=0, chunk_index=0, total_chunks=1)
    c2 = Chunk(content="Fact B", source="doc2.pdf", page=0, chunk_index=0, total_chunks=1)
    r1 = SearchResult(chunk=c1, score=0.9, rank=0)
    r2 = SearchResult(chunk=c2, score=0.8, rank=1)
    return MockRetriever(RetrievalResult(query="test", results=[r1, r2]))

def test_empty_context_abstains(empty_retriever):
    generator = MockGenerator(gate_response="YES") # Should not even be called
    pipeline = RAGPipeline(retriever=empty_retriever, generator=generator)
    
    resp = pipeline.ask("test question")
    assert "couldn't find enough information" in resp.answer
    assert resp.model == "abstention"
    assert not generator.generate_called

def test_high_confidence_bypasses_gate_and_generates(high_confidence_retriever):
    generator = MockGenerator(gate_response="NO") # Should not be called
    pipeline = RAGPipeline(retriever=high_confidence_retriever, generator=generator)
    
    resp = pipeline.ask("test question")
    assert resp.answer == "Generated Answer"
    assert generator.generate_called
    assert not generator._client.chat.completions.create.called

def test_low_confidence_bypasses_gate_and_abstains(low_confidence_retriever):
    generator = MockGenerator(gate_response="YES") # Should not be called
    pipeline = RAGPipeline(retriever=low_confidence_retriever, generator=generator)
    
    resp = pipeline.ask("test question")
    assert "couldn't find enough information" in resp.answer
    assert not generator.generate_called
    assert not generator._client.chat.completions.create.called

def test_borderline_unsupported_question_abstains(borderline_retriever):
    generator = MockGenerator(gate_response="NO, the context does not support it.")
    pipeline = RAGPipeline(retriever=borderline_retriever, generator=generator)
    
    resp = pipeline.ask("test question")
    assert "couldn't find enough information" in resp.answer
    assert "gate" in resp.model
    assert not generator.generate_called
    assert generator._client.chat.completions.create.called

def test_borderline_supported_question_generates_answer(borderline_retriever):
    generator = MockGenerator(gate_response="YES, the context has the facts.")
    pipeline = RAGPipeline(retriever=borderline_retriever, generator=generator)
    
    resp = pipeline.ask("test question")
    assert resp.answer == "Generated Answer"
    assert generator.generate_called
    assert generator._client.chat.completions.create.called

def test_multi_document_supported_question_generates_answer(multi_doc_retriever):
    generator = MockGenerator(gate_response="YES")
    pipeline = RAGPipeline(retriever=multi_doc_retriever, generator=generator)
    
    resp = pipeline.ask("compare facts", document_ids=["doc1", "doc2"])
    assert resp.answer == "Generated Answer"
    assert generator.generate_called
    assert multi_doc_retriever.kwargs.get("document_ids") == ["doc1", "doc2"]

def test_document_scope_is_preserved(high_confidence_retriever):
    generator = MockGenerator(gate_response="YES")
    pipeline = RAGPipeline(retriever=high_confidence_retriever, generator=generator)
    
    pipeline.ask("test", document_ids=["doc1"])
    assert high_confidence_retriever.kwargs.get("document_ids") == ["doc1"]

def test_gate_error_defaults_to_generation(borderline_retriever):
    generator = MockGenerator(gate_response="YES")
    # Break the gate intentionally
    generator._client.chat.completions.create.side_effect = Exception("API Error")
    
    pipeline = RAGPipeline(retriever=borderline_retriever, generator=generator)
    resp = pipeline.ask("test question")
    
    # Should fallback to generating if gate errors
    assert resp.answer == "Generated Answer"
    assert generator.generate_called
