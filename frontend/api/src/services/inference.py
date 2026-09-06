import json
from typing import AsyncGenerator, Dict, List, Optional
from uuid import UUID
from src.core.config import get_settings
from src.domain.citation import GROUNDED_SYSTEM_PROMPT, create_citations_from_chunks
from src.domain.models import Citation, DocumentChunk
from src.infrastructure.groq_client import GroqClient
from src.services.retrieval import RetrievalService


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
                    "content": f"The user asked: '{question}'. However, no relevant passages were found in the uploaded documents. Respond explaining that the provided document passages do not contain information to answer this question.",
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

        messages = self.build_rag_prompt(question, chunks, citations)
        
        token_count = 0
        try:
            async for token in self.llm.stream_chat(messages, model=model):
                token_count += 1
                yield {"event": "token", "token": token}
        except Exception as e:
            yield {"event": "error", "detail": str(e)}

        yield {
            "event": "done",
            "finish_reason": "stop",
            "total_tokens": token_count,
            "citations_count": len(citations),
        }
