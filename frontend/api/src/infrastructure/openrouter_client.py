import json
from typing import AsyncGenerator, Dict, List, Optional
import httpx
from src.core.config import get_settings
from src.infrastructure.interfaces import BaseLLMClient

class OpenRouterClient(BaseLLMClient):
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.OPENROUTER_API_KEY
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.fallback_models = [
            "liquid/lfm-2.5-2.6b:free",
            "nvidia/nemotron-3.5-lightning:free",
            "minimax/minimax-m3:free",
        ]

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.1,
    ) -> AsyncGenerator[str, None]:
        models_to_try = [model] if model and model not in self.fallback_models else []
        models_to_try.extend([m for m in self.fallback_models if m not in models_to_try])

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
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", self.base_url, headers=headers, json=payload) as response:
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
