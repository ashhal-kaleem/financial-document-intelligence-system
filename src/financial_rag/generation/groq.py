"""Groq API-backed generator (OpenAI-compatible interface)."""

from __future__ import annotations

from collections.abc import Iterator

from financial_rag.generation.base import BaseGenerator
from financial_rag.generation.models import ConversationTurn, GenerationResult
from financial_rag.retrieval.models import RetrievalResult

try:
    import groq as _groq_lib
    _GROQ_AVAILABLE = True
except ImportError:
    _groq_lib = None  # type: ignore[assignment]
    _GROQ_AVAILABLE = False

_SYSTEM_PROMPT = """\
You are a financial analyst assistant specialising in bank annual reports.

Your only job is to answer the question using the numbered context blocks provided.
Hard rules — every violation lowers your faithfulness score:
1. Every sentence must be traceable to a [N] block. Cite inline with [N].
2. Do NOT add general knowledge, background, or context not present in the blocks.
3. Do NOT infer, extrapolate, or synthesize beyond what is literally stated.
4. Do NOT round numbers, paraphrase statistics, or add qualifiers not in the source.
5. If the blocks lack information to answer fully, state exactly what is missing.
6. ALWAYS respond in clear English, regardless of the language of the source documents.\
"""

_NO_CONTEXT_ANSWER = (
    "No relevant information was found in the documents to answer this question."
)

_DEFAULT_MODEL = "llama-3.3-70b-versatile"
_MAX_TOKENS = 2048

AVAILABLE_GROQ_MODELS = [
    "openai/gpt-oss-20b",       # currently active in .env (Groq OpenAI-compat route)
    "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile",
    "llama-3.1-70b-versatile",
    "mixtral-8x7b-32768",
]


class GroqGenerator(BaseGenerator):
    """Generates grounded answers using the Groq API (OpenAI-compatible).

    Groq provides ultra-fast inference via hardware-accelerated LPUs.
    The API is OpenAI-compatible — messages/roles work identically.

    Args:
        model: Groq model ID (default: llama-3.1-8b-instant).
        api_key: Groq API key. Reads GROQ_API_KEY env var if None.
        max_tokens: Maximum output tokens per response.
        _client: Inject a pre-built client (for unit tests — avoids API calls).
    """

    def __init__(
        self,
        model: str = _DEFAULT_MODEL,
        api_key: str | None = None,
        max_tokens: int = _MAX_TOKENS,
        _client: object | None = None,
    ) -> None:
        if not _GROQ_AVAILABLE and _client is None:
            raise ImportError(
                "The 'groq' package is required for GroqGenerator. "
                "Install it with: pip install groq"
            )
        self._model = model
        self._max_tokens = max_tokens
        self._client = _client or _groq_lib.Groq(api_key=api_key)
        self._system = _SYSTEM_PROMPT

    def generate(
        self,
        retrieval_result: RetrievalResult,
        history: list[ConversationTurn] | None = None,
        model: str | None = None,
    ) -> GenerationResult:
        if retrieval_result.is_empty:
            return GenerationResult(
                answer=_NO_CONTEXT_ANSWER,
                query=retrieval_result.query,
                citations=[],
                model=self._model,
            )

        response = self._client.chat.completions.create(
            model=model or self._model,
            max_tokens=self._max_tokens,
            messages=self._build_messages(retrieval_result, history),
        )

        return GenerationResult(
            answer=response.choices[0].message.content,
            query=retrieval_result.query,
            citations=retrieval_result.citations,
            model=model or self._model,
            input_tokens=response.usage.prompt_tokens if response.usage else 0,
            output_tokens=response.usage.completion_tokens if response.usage else 0,
        )

    def stream(
        self,
        retrieval_result: RetrievalResult,
        history: list[ConversationTurn] | None = None,
        model: str | None = None,
    ) -> Iterator[str]:
        """Stream response tokens for the given retrieval result."""
        if retrieval_result.is_empty:
            yield _NO_CONTEXT_ANSWER
            return

        messages = [{"role": "system", "content": self._system}]
        messages += self._build_messages(retrieval_result, history)

        response = self._client.chat.completions.create(
            model=model or self._model,
            max_tokens=self._max_tokens,
            messages=messages,
            stream=True,
        )
        for chunk in response:
            token = chunk.choices[0].delta.content if chunk.choices else None
            if token:
                yield token

    def _build_messages(
        self,
        retrieval_result: RetrievalResult,
        history: list[ConversationTurn] | None = None,
    ) -> list[dict]:
        messages: list[dict] = [{"role": "system", "content": self._system}]
        for turn in (history or []):
            messages.append({"role": turn.role, "content": turn.content})
        messages.append({
            "role": "user",
            "content": f"{self._format_context(retrieval_result)}\n\nQuestion: {retrieval_result.query}",
        })
        return messages

    def _format_context(self, retrieval_result: RetrievalResult) -> str:
        lines = ["Context:"]
        for i, result in enumerate(retrieval_result.results, start=1):
            lines.append(f"[{i}] {result.citation}")
            lines.append(result.chunk.content.strip())
            lines.append("")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"GroqGenerator(model={self._model!r}, max_tokens={self._max_tokens})"
