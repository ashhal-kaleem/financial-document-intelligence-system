"""Signed retrieval receipts for optional user-authorized browser AI.

Receipts bind retrieved citation IDs to an owner, not the answer's truth or provider provenance.
No answer supplied by a browser is trusted as proof of model execution.
"""
import base64
import hashlib
import hmac
import json
import time
import httpx
from src.core.config import get_settings
from src.domain.citation import validate_answer_citations
from src.domain.models import Citation
from src.core.errors import FDISException

PUTER_MODELS = {
    'openrouter:google/gemma-4-31b-it:free': 'Gemma 4 31B (free variant)',
    'infron:qwen/qwen3.8-27b:free': 'Qwen 3.8 27B (free variant)',
    'openrouter:nvidia/nemotron-3.5-lightning:free': 'Nemotron 3.5 Lightning (free variant)',
}
CATALOG_URL = 'https://api.puter.com/puterai/chat/models/details'


def _signature(body: bytes) -> str:
    # Domain-separated HMAC. Never return the service key or share it with Puter/browser.
    key = get_settings().SUPABASE_SERVICE_ROLE_KEY.encode()
    return hmac.new(key, b'fdis-browser-ai-receipt-v1:' + body, hashlib.sha256).hexdigest()


def make_receipt(owner_id: str, citations: list[Citation], model: str) -> str:
    body = json.dumps({'owner': owner_id, 'expires': int(time.time()) + 600, 'model': model,
                       'citations': [c.model_dump(mode='json') for c in citations]}, separators=(',', ':')).encode()
    return base64.urlsafe_b64encode(body).decode().rstrip('=') + '.' + _signature(body)


def validate_receipt(receipt: str, owner_id: str, answer: str) -> list[Citation]:
    try:
        encoded, signature = receipt.split('.')
        body = base64.urlsafe_b64decode(encoded + '=' * (-len(encoded) % 4))
        if not hmac.compare_digest(signature, _signature(body)):
            raise ValueError()
        data = json.loads(body)
        if data['owner'] != owner_id or data['expires'] < time.time() or data['model'] not in PUTER_MODELS:
            raise ValueError()
        citations = [Citation(**c) for c in data['citations']]
    except (ValueError, KeyError, TypeError):
        raise FDISException('Invalid AI session', 'AI context expired or is invalid. Ask again.', 422, 'invalid_ai_receipt') from None
    if not validate_answer_citations(answer, citations):
        raise FDISException('Invalid citations', 'Answer lacks valid source markers. Retry or inspect the PDF.', 422, 'invalid_citations')
    return citations


async def verify_free_model(model: str) -> None:
    if model not in PUTER_MODELS:
        raise FDISException('Model not enabled', 'Choose an enabled free model.', 422, 'model_not_enabled')
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(CATALOG_URL)
            response.raise_for_status()
            models = response.json()['models']
        entry = next(m for m in models if m.get('id') == model)
        costs = entry['costs']
        input_key, output_key = entry['input_cost_key'], entry['output_cost_key']
        # Missing price metadata is not proof of zero cost. Any new nonzero usage rate fails closed.
        if costs[input_key] != 0 or costs[output_key] != 0:
            raise ValueError()
        if any(value != 0 for key, value in costs.items() if key != 'tokens'):
            raise ValueError()
    except Exception:
        raise FDISException('Free model unavailable', 'The selected free model could not be verified. No paid fallback was used.', 503, 'free_model_unverified') from None
