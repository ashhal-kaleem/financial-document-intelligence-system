from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from src.core.auth import AuthUser
from src.core.rate_limit import rate_limited_user
from src.domain.models import AskRequest
from src.services.inference import InferenceService

router = APIRouter(prefix="/ask", tags=["Financial Q&A"])
inference_service = InferenceService()

@router.post("/context")
async def get_ask_context(payload: AskRequest, user: AuthUser = Depends(rate_limited_user)):
    """
    RAG Context Endpoint: Returns grounded context passages, citations, and prompt.
    Authenticated inspection of retrieved passages; answers are produced by the user-authorized browser AI flow.
    """
    chunks = await inference_service.retrieval.retrieve_relevant_chunks(
        query=payload.question,
        document_ids=payload.document_ids,
        owner_id=user.id,
    )
    citations = inference_service.retrieval.build_citations(chunks)
    messages = inference_service.build_rag_prompt(payload.question, chunks, citations)

    return {
        "success": True,
        "data": {
            "messages": messages,
            "citations": [c.model_dump() for c in citations],
            "chunks_count": len(chunks),
        },
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": "/api/v1/ask/context",
        },
    }

# User-authorized browser provider boundary. No Puter token is accepted by this backend.
from src.domain.models import BrowserAIRequest, BrowserAIValidation
from src.domain.citation import NOT_COVERED_ANSWER
from src.services.browser_ai import PUTER_MODELS, make_receipt, validate_receipt, verify_free_model

@router.get('/browser-models')
async def browser_models(user: AuthUser = Depends(rate_limited_user)):
    return {'models': [{'id': k, 'name': v} for k, v in PUTER_MODELS.items()]}

@router.post('/browser-context')
async def browser_context(payload: BrowserAIRequest, user: AuthUser = Depends(rate_limited_user)):
    if not payload.consent:
        raise HTTPException(422, 'Consent to the provider disclosure is required.')
    if payload.model not in PUTER_MODELS:
        raise HTTPException(422, 'Requested model is not enabled.')
    chunks = await inference_service.retrieval.retrieve_relevant_chunks(
        query=payload.question, document_ids=payload.document_ids, owner_id=user.id)
    citations = inference_service.retrieval.build_citations(chunks)
    if not chunks:
        return {'data': {'answer': NOT_COVERED_ANSWER, 'citations': [], 'messages': [], 'receipt': None}}
    await verify_free_model(payload.model)
    return {'data': {
        'messages': inference_service.build_rag_prompt(payload.question, chunks, citations),
        'citations': [c.model_dump(mode='json') for c in citations],
        'receipt': make_receipt(user.id, citations, payload.model),
    }}

@router.post('/browser-validate')
async def browser_validate(payload: BrowserAIValidation, user: AuthUser = Depends(rate_limited_user)):
    citations = validate_receipt(payload.receipt, user.id, payload.answer)
    # Check ownership/status again: a previously visible report may have been deleted since retrieval.
    visible = set(await inference_service.retrieval.supabase.get_visible_document_ids(user.id))
    if any(c.document_id not in visible for c in citations):
        raise HTTPException(409, 'Source document is no longer available. Ask again.')
    return {'data': {'citation_ids_valid': True, 'semantic_support_verified': False}}
