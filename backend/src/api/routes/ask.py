import json
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from src.domain.models import AskRequest
from src.services.inference import InferenceService

router = APIRouter(prefix="/ask", tags=["Financial Q&A"])
inference_service = InferenceService()

@router.post("/stream")
async def ask_stream(payload: AskRequest, request: Request):
    async def event_generator():
        try:
            async for event_data in inference_service.stream_answer(
                question=payload.question,
                document_ids=payload.document_ids,
                model=payload.model,
            ):
                # SSE Disconnect Defense Guard: Abort immediately if client tab closes
                if await request.is_disconnected():
                    break
                yield f"data: {json.dumps(event_data)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            error_payload = {"event": "error", "detail": str(e)}
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
