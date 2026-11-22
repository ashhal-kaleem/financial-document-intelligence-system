"""Server-side answer generation on Groq's free plan.

The API key never leaves the server. Only the question and the retrieved
passages of the caller's own documents are sent. There is no paid fallback:
quota and provider failures surface as honest, retryable errors.
"""
import logging
import httpx
from src.core.config import get_settings
from src.core.errors import FDISException

logger = logging.getLogger(__name__)

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
MAX_ANSWER_CHARS = 60000


def _not_configured() -> FDISException:
    return FDISException(
        "AI answers not configured",
        "AI answers are being set up on this deployment. Try again shortly.",
        503,
        "ai_not_configured",
    )


class GroqClient:
    def __init__(self):
        self.settings = get_settings()

    async def complete(self, messages: list[dict]) -> str:
        """One non-streamed completion; returns the answer text or raises FDISException."""
        key = self.settings.GROQ_API_KEY
        if not key:
            raise _not_configured()
        payload = {
            "model": self.settings.GROQ_MODEL,  # server-pinned; callers cannot pick models
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": self.settings.LLM_MAX_OUTPUT_TOKENS,
            # gpt-oss is a reasoning model: reasoning tokens share the max_tokens
            # budget. Low effort keeps short extractive Q&A inside the budget
            # (Groq-docs supported parameter for openai/gpt-oss-*).
            "reasoning_effort": "low",
            "stream": False,
        }
        try:
            async with httpx.AsyncClient(timeout=self.settings.GROQ_TIMEOUT_SECONDS) as client:
                res = await client.post(
                    GROQ_CHAT_URL,
                    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                    json=payload,
                )
        except httpx.HTTPError:
            logger.warning("Groq request failed to complete")
            raise FDISException(
                "AI unavailable",
                "The free AI service could not be reached. Retry in a moment. No paid fallback was used.",
                503,
                "ai_unavailable",
            ) from None
        if res.status_code == 429:
            retry_after = res.headers.get("retry-after")
            detail = "Today's free AI quota is exhausted. Try again later. No paid fallback was used."
            if retry_after and retry_after.isdigit() and int(retry_after) < 600:
                detail = f"The free AI service is rate limited. Retry in about {retry_after} seconds. No paid fallback was used."
            raise FDISException("Free quota exhausted", detail, 429, "free_quota_exhausted")
        if res.status_code in (401, 403):
            logger.warning("Groq rejected the configured key (%s)", res.status_code)
            raise _not_configured()
        if res.status_code >= 400:
            logger.warning("Groq returned %s", res.status_code)
            raise FDISException(
                "AI unavailable",
                "The free AI service returned an error. Retry in a moment. No paid fallback was used.",
                503,
                "ai_unavailable",
            )
        try:
            choice = res.json()["choices"][0]
            answer = choice["message"]["content"]
            finish = choice.get("finish_reason")
        except (ValueError, KeyError, IndexError, TypeError):
            logger.warning("Groq returned an unreadable response")
            raise FDISException(
                "AI unavailable",
                "The free AI service returned an unreadable response. Retry. No paid fallback was used.",
                503,
                "ai_unavailable",
            ) from None
        if finish != "stop" or not isinstance(answer, str) or not answer.strip() or len(answer) > MAX_ANSWER_CHARS:
            usage = res.json().get("usage") if isinstance(res.json(), dict) else None
            logger.warning(
                "Groq answer rejected: finish_reason=%s answer_chars=%s usage=%s",
                finish,
                len(answer) if isinstance(answer, str) else None,
                usage,
            )
            raise FDISException(
                "Incomplete answer",
                "I couldn't put together a complete answer just now. Please ask the question again.",
                502,
                "incomplete_answer",
            )
        return answer
