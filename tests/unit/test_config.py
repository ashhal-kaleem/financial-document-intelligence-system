"""Smoke tests for project setup and configuration."""

from financial_rag import __version__
from financial_rag.config import Settings


def test_version():
    assert __version__ == "0.1.0"


def test_settings_defaults(monkeypatch):
    monkeypatch.delenv("LLM_BACKEND", raising=False)
    s = Settings(_env_file=None)
    assert s.llm_backend == "mock"
    assert s.chunk_size == 512
    assert s.chunk_overlap == 64
    assert s.retrieval_top_k == 5


def test_settings_override(monkeypatch):
    monkeypatch.setenv("CHUNK_SIZE", "256")
    monkeypatch.setenv("LLM_BACKEND", "groq")
    s = Settings()
    assert s.chunk_size == 256
    assert s.llm_backend == "groq"
