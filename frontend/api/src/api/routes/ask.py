import json
from datetime import datetime, timezone
import logging
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import StreamingResponse
from src.core.auth import AuthUser
from src.core.rate_limit import rate_limited_user
from src.domain.models import AskRequest
from src.services.inference import InferenceService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ask", tags=["Financial Q&A"])
inference_service = InferenceService()

@router.post("/context")
async def get_ask_context(payload: AskRequest, user: AuthUser = Depends(rate_limited_user)):
    """
    RAG Context Endpoint: Returns grounded context passages, citations, and prompt.
    Authenticated inspection of retrieved passages; the app answers through the backend stream.
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

@router.post("/stream")
async def ask_stream(payload: AskRequest, request: Request, user: AuthUser = Depends(rate_limited_user)):
    """
    Backend Stream Endpoint: Server-side SSE inference fallback using Groq / OpenRouter.
    """
    if payload.model and payload.model != inference_service.settings.GROQ_MODEL:
        raise HTTPException(status_code=422, detail="Requested model is not enabled.")

    async def event_generator():
        try:
            async for event_data in inference_service.stream_answer(
                question=payload.question,
                document_ids=payload.document_ids,
                model=payload.model,
                owner_id=user.id,
            ):
                if await request.is_disconnected():
                    break
                yield f"data: {json.dumps(event_data)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception:
            logger.warning("Ask stream failed")
            error_payload = {"event": "error", "detail": "The answer service failed. Please try again."}
            yield f"data: {json.dumps(error_payload)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
