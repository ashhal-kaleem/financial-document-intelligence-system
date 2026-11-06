import json
import logging
from typing import AsyncGenerator, Dict, List, Optional
import httpx
from src.core.config import get_settings
from src.infrastructure.interfaces import BaseLLMClient
from src.infrastructure.openrouter_client import OpenRouterClient
from src.infrastructure.llm_stream import stream_tokens

logger = logging.getLogger(__name__)


class GroqClient(BaseLLMClient):
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.GROQ_API_KEY
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.default_model = self.settings.GROQ_MODEL
        self.fallback_client = OpenRouterClient()

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.1,
    ) -> AsyncGenerator[str, None]:
        target_model = model or self.default_model
        if target_model != self.default_model:
            raise ValueError("Model is not enabled")
        if not self.api_key:
            raise RuntimeError("Backend answer provider is not configured")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": target_model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
            "max_tokens": self.settings.LLM_MAX_OUTPUT_TOKENS,
        }

        emitted = False
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=10.0)) as client:
                async with client.stream("POST", self.base_url, headers=headers, json=payload) as response:
                    response.raise_for_status()
                    async for token in stream_tokens(response):
                        emitted = True
                        yield token
        except Exception:
            # Never concatenate a second model's answer onto a partial first answer.
            if emitted or not self.settings.LLM_FALLBACK_ENABLED or not self.settings.OPENROUTER_API_KEY:
                raise RuntimeError("Answer provider failed") from None
            logger.warning("Primary provider unavailable; using configured fallback")
            async for token in self.fallback_client.stream_chat(messages, temperature=temperature):
                yield token
