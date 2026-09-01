"""Factory to build generators from configuration."""

from __future__ import annotations

from financial_rag.generation.base import BaseGenerator
from financial_rag.generation.groq import AVAILABLE_GROQ_MODELS, GroqGenerator
from financial_rag.generation.mock import MockGenerator


def create_generator(
    model: str = "llama-3.1-8b-instant",
    backend: str = "groq",
    api_key: str | None = None,
    **_kwargs,
) -> BaseGenerator:
    """Build a generator ready to use.

    Args:
        model: Groq model identifier.
            Options: llama-3.1-8b-instant (fast), llama-3.3-70b-versatile (quality).
        backend: "groq" (Groq API) or "mock" (testing / offline).
        api_key: Groq API key.  Reads GROQ_API_KEY env var if None.

    Returns:
        Ready-to-use generator implementing BaseGenerator.

    Raises:
        ValueError: If the model or backend is unknown.
    """
    if backend == "mock":
        return MockGenerator()

    if backend == "groq":
        if model not in AVAILABLE_GROQ_MODELS:
            raise ValueError(
                f"Unknown model: '{model}'. Available: {AVAILABLE_GROQ_MODELS}"
            )
        return GroqGenerator(model=model, api_key=api_key)

    raise ValueError(f"Unknown backend: '{backend}'. Choose 'groq' or 'mock'.")
