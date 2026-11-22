import logging
from typing import Dict, List
from src.domain.citation import GROUNDED_SYSTEM_PROMPT, NOT_COVERED_ANSWER
from src.domain.models import Citation, DocumentChunk
from src.services.retrieval import RetrievalService

logger = logging.getLogger(__name__)


class InferenceService:
    """Shared retrieval and grounded prompt assembly for the Q&A route.

    MiniLM embeddings retrieve passages; one server-side completion on the
    configured free Groq model turns them into the cited answer.
    """

    def __init__(self, retrieval_service: RetrievalService = None):
        self.retrieval = retrieval_service or RetrievalService()

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
