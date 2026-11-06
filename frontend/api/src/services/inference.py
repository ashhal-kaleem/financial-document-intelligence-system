import json
import logging
from typing import AsyncGenerator, Dict, List, Optional
from uuid import UUID
from src.core.config import get_settings
from src.domain.citation import GROUNDED_SYSTEM_PROMPT, NOT_COVERED_ANSWER, create_citations_from_chunks, validate_answer_citations
from src.domain.models import Citation, DocumentChunk
from src.infrastructure.groq_client import GroqClient
from src.services.retrieval import RetrievalService

logger = logging.getLogger(__name__)


class InferenceService:
    def __init__(
        self,
        retrieval_service: RetrievalService = None,
        llm_client: GroqClient = None,
    ):
        self.settings = get_settings()
        self.retrieval = retrieval_service or RetrievalService()
        self.llm = llm_client or GroqClient()

    def build_rag_prompt(self, question: str, chunks: List[DocumentChunk], citations: List[Citation]) -> List[Dict[str, str]]:
        if not chunks:
            # If no context found above similarity threshold
            return [
                {"role": "system", "content": GROUNDED_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"No relevant passages were found in the uploaded documents for the user's question. Reply with exactly this sentence and nothing else: {NOT_COVERED_ANSWER}",
                },
            ]

        context_blocks = []
        for c, cit in zip(chunks, citations):
            context_blocks.append(
                f"[{cit.citation_id}] Document: {cit.filename}, Page: {cit.page} (Chunk {cit.chunk_index + 1}/{cit.total_chunks})\n{c.content}"
            )

        context_str = "\n\n".join(context_blocks)
        user_prompt = f"""CONTEXT PASSAGES FROM UPLOADED DOCUMENT(S):
----------------------------------------
{context_str}
----------------------------------------

USER INQUIRY:
{question}

Provide an accurate, comprehensive, and grounded answer strictly citing relevant passages using [1], [2], etc. If the user asks to read, summarize, or explain the document, summarize and explain what is disclosed in these passages clearly and helpfully. If specific facts or metrics requested are not mentioned anywhere in the excerpts, state that they are not disclosed."""

        return [
            {"role": "system", "content": GROUNDED_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

    async def stream_answer(
        self,
        question: str,
        document_ids: Optional[List[UUID]] = None,
        model: Optional[str] = None,
        owner_id: Optional[str] = None,
    ) -> AsyncGenerator[Dict, None]:
        """
        Orchestrates full RAG streaming pipeline:
        Yields:
        1. {"event": "stage", "stage": "retrieving", ...}
        2. {"event": "citations", "citations": [...]}
        3. {"event": "token", "token": "..."}
        4. {"event": "done", ...}
        """
        # 1. Retrieval stage
        yield {
            "event": "stage",
            "stage": "retrieving",
            "detail": "Searching pgvector index for matching passages...",
        }

        chunks = await self.retrieval.retrieve_relevant_chunks(
            query=question,
            document_ids=document_ids,
            owner_id=owner_id,
        )
        citations = self.retrieval.build_citations(chunks)

        # 2. Citations stage
        yield {
            "event": "citations",
            "citations": [c.model_dump(mode="json") for c in citations],
        }

        # 3. Generating stage
        yield {
            "event": "stage",
            "stage": "generating",
            "detail": "Streaming grounded response from Groq LPU...",
        }

        if not chunks:
            # Nothing relevant retrieved: answer with a fixed sentence. The model is never asked to guess.
            yield {"event": "token", "token": NOT_COVERED_ANSWER}
            yield {"event": "done", "finish_reason": "not_covered", "stream_chunks": 1, "citations_count": 0}
            return

        messages = self.build_rag_prompt(question, chunks, citations)
        
        token_count = 0
        answer_parts = []
        try:
            async for token in self.llm.stream_chat(messages, model=model):
                token_count += 1
                answer_parts.append(token)
                yield {"event": "token", "token": token}
        except Exception as e:
            logger.warning("Answer stream failed")
            yield {"event": "error", "detail": "The answer service failed. Please try again."}
            return

        if not validate_answer_citations("".join(answer_parts), citations):
            yield {"event": "error", "detail": "The answer did not include valid source citations. Please retry."}
            return

        yield {
            "event": "done",
            "finish_reason": "stop",
            "stream_chunks": token_count,
            "citations_count": len(citations),
        }
