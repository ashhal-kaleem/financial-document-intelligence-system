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


GROUNDED_SYSTEM_PROMPT = """You are an elite financial analyst and corporate auditor AI for the Financial Document Intelligence System (FDIS).
Your task is to answer questions regarding corporate annual reports, 10-Ks, balance sheets, and footnotes strictly based on the provided context passages.

STRICT GROUNDING & ZERO-HALLUCINATION RULES:
1. Ground every claim directly in the provided context. If a metric, footnote, or date is not explicitly stated in the context, DO NOT GUESS OR ESTIMATE. State clearly: "The provided financial document does not disclose this information."
2. Whenever you use information from a context chunk, cite it using its exact citation marker like [1], [2], etc.
3. Preserve all financial precision (e.g. "$391,035 million", "31.2% operating margin", "GAAP diluted EPS of $6.08"). Never round numbers unless instructed.
4. If comparing balance sheet or cash flow periods, specify the exact fiscal year or quarter stated in the text.
"""
