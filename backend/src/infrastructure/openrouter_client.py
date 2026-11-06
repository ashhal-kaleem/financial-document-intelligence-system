import json
from typing import AsyncGenerator, Dict, List, Optional
import httpx
from src.core.config import get_settings
from src.infrastructure.interfaces import BaseLLMClient
from src.infrastructure.llm_stream import stream_tokens

class OpenRouterClient(BaseLLMClient):
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.OPENROUTER_API_KEY
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.fallback_models = [self.settings.OPENROUTER_DEFAULT_MODEL]

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.1,
    ) -> AsyncGenerator[str, None]:
        if not self.settings.LLM_FALLBACK_ENABLED or not self.api_key:
            raise RuntimeError("Fallback is not enabled")
        if model and model != self.settings.OPENROUTER_DEFAULT_MODEL:
            raise ValueError("Model is not enabled")
        models_to_try = self.fallback_models

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://fdis.local",
            "X-Title": "FDIS",
        }
        # Pass prioritized fallback array to OpenRouter
        payload = {
            "models": models_to_try,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
            "max_tokens": self.settings.LLM_MAX_OUTPUT_TOKENS,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", self.base_url, headers=headers, json=payload) as response:
                response.raise_for_status()
                async for token in stream_tokens(response):
                    yield token
