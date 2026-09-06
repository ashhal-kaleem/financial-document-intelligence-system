import json
import logging
from typing import AsyncGenerator, Dict, List, Optional
import httpx
from src.core.config import get_settings
from src.infrastructure.interfaces import BaseLLMClient
from src.infrastructure.openrouter_client import OpenRouterClient

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
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": target_model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }

        used_fallback = False
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                async with client.stream("POST", self.base_url, headers=headers, json=payload) as response:
                    if response.status_code in (429, 500, 502, 503, 504):
                        logger.warning(f"Groq returned {response.status_code}, shifting quota to OpenRouter fallback...")
                        used_fallback = True
                    else:
                        response.raise_for_status()
                        async for line in response.aiter_lines():
                            line = line.strip()
                            if not line or not line.startswith("data: "):
                                continue
                            data_str = line[6:].strip()
                            if data_str == "[DONE]":
                                break
                            try:
                                parsed = json.loads(data_str)
                                delta = parsed.get("choices", [{}])[0].get("delta", {})
                                content = delta.get("content")
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                continue
        except (httpx.HTTPError, Exception) as exc:
            logger.warning(f"Groq request failed ({exc}), falling back to OpenRouter...")
            used_fallback = True

        if used_fallback:
            async for token in self.fallback_client.stream_chat(messages, temperature=temperature):
                yield token
