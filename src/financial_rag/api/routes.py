"""API route handlers."""

import json
import time
from collections.abc import Generator

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from financial_rag.api.schemas import (
    AskRequest,
    AskResponse,
    HealthResponse,
    ModelsResponse,
)
from financial_rag.generation.groq import AVAILABLE_GROQ_MODELS as AVAILABLE_MODELS
from financial_rag.generation.models import ConversationTurn
from financial_rag.api.upload import upload_router

router = APIRouter()
router.include_router(upload_router)


def _get_pipeline(request: Request):
    pipeline = request.app.state.pipeline
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized.")
    return pipeline


@router.post("/ask", response_model=AskResponse)
def ask(body: AskRequest, request: Request) -> AskResponse:
    """Answer a question using the RAG pipeline."""
    pipeline = _get_pipeline(request)
    history = [ConversationTurn(role=m.role, content=m.content) for m in body.history]
    try:
        response = pipeline.ask(
            question=body.question,
            top_k=body.top_k,
            source_filter=body.source_filter,
            document_ids=body.document_ids,
            history=history or None,
            model=body.model,
        )
    except Exception as exc:
        # Catch Groq RateLimitError (and any other LLM API error) and surface
        # a clean JSON 429/503 so callers can detect and retry without crashing.
        err_str = str(exc)
        if "rate_limit" in err_str.lower() or "429" in err_str or "RateLimitError" in type(exc).__name__:
            raise HTTPException(status_code=429, detail=f"LLM rate limit: {err_str[:200]}")
        raise HTTPException(status_code=503, detail=f"Pipeline error: {err_str[:200]}")
    return AskResponse(
        answer=response.answer,
        query=response.query,
        citations=response.citations,
        retrieval_scores=response.retrieval_scores,
        chunks_used=response.chunks_used,
        model=response.model,
        retrieval_ms=response.retrieval_ms,
        generation_ms=response.generation_ms,
        total_ms=response.total_ms,
        is_grounded=response.is_grounded,
    )


@router.post("/ask/stream")
def ask_stream(body: AskRequest, request: Request) -> StreamingResponse:
    """Stream answer tokens via Server-Sent Events."""
    pipeline = _get_pipeline(request)
    generator = pipeline._generator
    retriever = pipeline._retriever

    t0 = time.perf_counter()
    retrieve_kwargs = {"top_k": body.top_k}
    if body.source_filter:
        retrieve_kwargs["source_filter"] = body.source_filter
    if body.document_ids is not None:
        retrieve_kwargs["document_ids"] = body.document_ids
        
    retrieval = retriever.retrieve(
        body.question,
        **retrieve_kwargs,
    )
    retrieval_ms = (time.perf_counter() - t0) * 1000

    history = [ConversationTurn(role=m.role, content=m.content) for m in body.history]
    model_name = body.model or getattr(generator, "_model", "llama-3.1-8b-instant")

    def event_stream() -> Generator[str, None, None]:
        full_text = ""
        t1 = time.perf_counter()

        for token in generator.stream(retrieval, history=history or None, model=model_name):
            full_text += token
            yield f"data: {json.dumps({'token': token})}\n\n"

        generation_ms = (time.perf_counter() - t1) * 1000
        done_payload = {
            "done": True,
            "answer": full_text.strip(),
            "query": body.question,
            "citations": retrieval.citations,
            "retrieval_scores": [r.score for r in retrieval.results],
            "chunks_used": retrieval.total,
            "model": model_name,
            "retrieval_ms": retrieval_ms,
            "generation_ms": generation_ms,
            "total_ms": retrieval_ms + generation_ms,
            "is_grounded": retrieval.total > 0,
        }
        yield f"data: {json.dumps(done_payload)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        },
    )


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    """Return pipeline status and store statistics."""
    pipeline = _get_pipeline(request)
    store_chunks = pipeline._retriever.store_size
    model = type(pipeline._generator).__name__
    return HealthResponse(
        status="ok",
        model=model,
        store_chunks=store_chunks,
        store_path=str(request.app.state.store_path),
    )


@router.get("/models", response_model=ModelsResponse)
def models(request: Request) -> ModelsResponse:
    """List available Groq models and the currently active one."""
    pipeline = _get_pipeline(request)
    current = getattr(pipeline._generator, "_model", "unknown")
    return ModelsResponse(available=AVAILABLE_MODELS, current=current)
