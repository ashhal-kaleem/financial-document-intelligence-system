import pytest
from src.infrastructure.embedding_client import EmbeddingClient
from src.infrastructure.supabase_client import SupabaseClient
from src.infrastructure.groq_client import GroqClient
from src.infrastructure.resend_client import ResendClient


def test_embedding_client_dimensions():
    client = EmbeddingClient()
    texts = ["Operating cash flow reached $118 billion in 2024.", "Total liabilities $290B."]
    embeddings = client.embed_texts(texts)
    assert len(embeddings) == 2
    assert len(embeddings[0]) == 384
    assert len(embeddings[1]) == 384

    query_vec = client.embed_query("What was operating cash flow?")
    assert len(query_vec) == 384


def test_supabase_client_initialization():
    client = SupabaseClient()
    assert client.base_url.startswith("https://")
    assert "apikey" in client.headers
    assert "Authorization" in client.headers


def test_groq_client_initialization():
    client = GroqClient()
    assert client.api_key is not None
    assert client.default_model == "qwen/qwen3.8-27b"
    assert client.fallback_client is not None


def test_resend_client_initialization():
    client = ResendClient()
    assert client.api_key is not None
