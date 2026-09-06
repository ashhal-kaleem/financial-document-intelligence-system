import re
from typing import List
from src.domain.models import Citation, DocumentChunk


def create_citations_from_chunks(chunks: List[DocumentChunk]) -> List[Citation]:
    citations: List[Citation] = []
    for idx, chunk in enumerate(chunks, start=1):
        # Create a clean, representative snippet (up to 180 chars)
        cleaned_content = " ".join(chunk.content.split())
        snippet = cleaned_content[:180] + "..." if len(cleaned_content) > 180 else cleaned_content
        
        citations.append(
            Citation(
                citation_id=idx,
                document_id=chunk.document_id,
                filename=chunk.source,
                page=chunk.page,
                chunk_index=chunk.chunk_index,
                total_chunks=chunk.total_chunks,
                similarity=round(chunk.similarity or 0.0, 4),
                snippet=snippet,
            )
        )
    return citations


def format_citation_string(citation: Citation) -> str:
    """Standardized citation string: [1] filename, p.X (chunk Y/Z)"""
    return f"[{citation.citation_id}] {citation.filename}, p.{citation.page} (chunk {citation.chunk_index + 1}/{citation.total_chunks})"


GROUNDED_SYSTEM_PROMPT = """You are an advanced Document Intelligence & Analysis AI for the Financial Document Intelligence System (FDIS).
Your task is to analyze, explain, summarize, and answer questions regarding any uploaded documents—including corporate annual reports, SEC 10-Ks, financial statements, balance sheets, footnotes, as well as technical papers, project synopses, and academic/enterprise documents—strictly based on the provided context passages.

STRICT GROUNDING & ZERO-HALLUCINATION RULES:
1. Ground every claim directly in the provided context passages. Always answer the user's inquiry (e.g. read, explain, summarize, or extract specific information) thoroughly and helpfully using the context.
2. If the user asks for specific facts, metrics, or details that are not mentioned anywhere in the provided context, state clearly that the provided document passages do not contain that specific detail. Never refuse or reject a document simply because it is non-financial.
3. Whenever you reference or quote information from a context chunk, cite it using its exact citation marker like [1], [2], etc.
4. When dealing with financial numbers, preserve exact figures and precision (e.g., "$391,035 million", percentages, dates).
5. If the user asks in Hindi, Hinglish, or English (e.g., "isko read karo", "summarize this", "explain"), provide a clear, comprehensive, and well-structured response explaining what the document covers based on the cited excerpts.
"""
