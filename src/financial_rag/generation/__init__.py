"""Generation — LLM-backed answer synthesis from retrieved chunks."""

from financial_rag.generation.models import GenerationResult
from financial_rag.generation.base import BaseGenerator
from financial_rag.generation.groq import GroqGenerator, AVAILABLE_GROQ_MODELS
from financial_rag.generation.mock import MockGenerator
from financial_rag.generation.factory import create_generator

AVAILABLE_MODELS = AVAILABLE_GROQ_MODELS

__all__ = [
    "GenerationResult",
    "BaseGenerator",
    "GroqGenerator",
    "MockGenerator",
    "AVAILABLE_MODELS",
    "AVAILABLE_GROQ_MODELS",
    "create_generator",
]
