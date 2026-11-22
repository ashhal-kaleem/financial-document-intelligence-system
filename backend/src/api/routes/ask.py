from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from src.core.auth import AuthUser
from src.core.config import get_settings
from src.core.errors import FDISException
from src.core.rate_limit import rate_limited_user
from src.domain.citation import NOT_COVERED_ANSWER, normalize_citation_markers, validate_answer_citations
from src.domain.models import AskRequest
from src.infrastructure.groq_client import GroqClient
from src.infrastructure.supabase_client import SupabaseClient
from src.services.inference import InferenceService

router = APIRouter(prefix="/ask", tags=["Financial Q&A"])
inference_service = InferenceService()
supabase = SupabaseClient()
groq = GroqClient()


def _quota_error(kind: str) -> FDISException:
    if kind == "global_exhausted":
        return FDISException(
            "Free quota exhausted",
            "Today's shared free answer quota is full. Try again tomorrow. No paid fallback was used.",
            429,
            "free_quota_exhausted",
        )
    return FDISException(
        "Daily question limit reached",
        "You reached today's free question limit for this guest session. Try again tomorrow or end the session to clear your data.",
        429,
        "daily_question_limit",
    )


@router.post("/answer")
async def ask_answer(payload: AskRequest, user: AuthUser = Depends(rate_limited_user)):
    """Grounded answer: MiniLM retrieval over the caller's own documents, then one
    server-side completion on the configured free Groq model. Only the question and
    retrieved passages leave the server; the key and the PDF never do."""
    settings = get_settings()
    chunks = await inference_service.retrieval.retrieve_relevant_chunks(
        query=payload.question,
        document_ids=payload.document_ids,
        owner_id=user.id,
    )
    citations = inference_service.retrieval.build_citations(chunks)
    if not chunks:
        # No provider call, no quota spent: the documents simply do not cover this.
        return {
            "success": True,
            "data": {
                "answer": NOT_COVERED_ANSWER,
                "citations": [],
                "chunks_count": 0,
                "model": None,
            },
            "meta": {"timestamp": datetime.now(timezone.utc).isoformat(), "path": "/api/v1/ask/answer"},
        }

    quota = await supabase.take_question_quota(
        user.id, settings.GUEST_DAILY_QUESTION_LIMIT, settings.GLOBAL_DAILY_ANSWER_LIMIT
    )
    if quota != "ok":
        raise _quota_error(quota)

    messages = inference_service.build_rag_prompt(payload.question, chunks, citations)
    answer = normalize_citation_markers(await groq.complete(messages))
    if not validate_answer_citations(answer, citations):
        # One regeneration, then refuse: answers without valid source markers are
        # never shown as grounded output.
        answer = normalize_citation_markers(await groq.complete(messages))
        if not validate_answer_citations(answer, citations):
            raise FDISException(
                "Citation check failed",
                "The answer's source markers could not be verified. It was not shown. Ask again.",
                422,
                "invalid_citations",
            )

    return {
        "success": True,
        "data": {
            "answer": answer,
            "citations": [c.model_dump(mode="json") for c in citations],
            "chunks_count": len(chunks),
            "model": settings.GROQ_MODEL,
        },
        "meta": {"timestamp": datetime.now(timezone.utc).isoformat(), "path": "/api/v1/ask/answer"},
    }
