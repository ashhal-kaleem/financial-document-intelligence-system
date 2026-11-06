"""Strict provider SSE parsing. A disconnected or empty stream is not a successful answer."""
import json

async def stream_tokens(response):
    emitted = False
    async for line in response.aiter_lines():
        if not line.startswith('data:'):
            continue
        data = line[5:].strip()
        if data == '[DONE]':
            if not emitted:
                raise RuntimeError('Empty provider answer')
            return
        try:
            payload = json.loads(data)
        except json.JSONDecodeError:
            raise RuntimeError('Invalid provider stream') from None
        if payload.get('error'):
            raise RuntimeError('Provider stream error')
        choices = payload.get('choices') or []
        if choices:
            text = choices[0].get('delta', {}).get('content')
            if text:
                emitted = True
                yield text
    raise RuntimeError('Provider stream interrupted')
