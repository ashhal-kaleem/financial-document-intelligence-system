"""Deterministic mock generator for unit tests — no LLM API required."""

from collections.abc import Iterator

from financial_rag.generation.base import BaseGenerator
from financial_rag.generation.models import ConversationTurn, GenerationResult
from financial_rag.retrieval.models import RetrievalResult


class MockGenerator(BaseGenerator):
    """Returns a fixed answer without calling any LLM.

    Uses the text hash of the query as a seed so behavior is deterministic.
    Designed for unit tests that need a generator without an LLM API call.

    Args:
        answer: The fixed string to return as the answer.
    """

    def __init__(self, answer: str = "Respuesta de prueba basada en el contexto.") -> None:
        self._answer = answer

    def generate(
        self,
        retrieval_result: RetrievalResult,
        history: list[ConversationTurn] | None = None,
        model: str | None = None,
    ) -> GenerationResult:
        return GenerationResult(
            answer=self._answer,
            query=retrieval_result.query,
            citations=retrieval_result.citations,
            model="mock",
            input_tokens=len(retrieval_result.query.split()),
            output_tokens=len(self._answer.split()),
        )

    def stream(
        self,
        retrieval_result: RetrievalResult,
        history: list[ConversationTurn] | None = None,
        model: str | None = None,
    ) -> Iterator[str]:
        yield self._answer
