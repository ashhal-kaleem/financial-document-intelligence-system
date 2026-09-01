"""Data model for a full RAG pipeline response."""

from dataclasses import dataclass, field


@dataclass
class RAGResponse:
    """The consolidated output of one RAG pipeline call.

    Combines retrieval and generation results into a single object for
    consumption by API endpoints, UIs, and evaluation pipelines.
    """

    answer: str
    query: str
    citations: list[str]
    retrieval_scores: list[float]
    chunks_used: int
    model: str
    retrieval_ms: float
    generation_ms: float
    chunk_texts: list[str] = field(default_factory=list)

    @property
    def total_ms(self) -> float:
        return self.retrieval_ms + self.generation_ms

    @property
    def is_grounded(self) -> bool:
        """True if the answer is backed by at least one retrieved chunk."""
        return self.chunks_used > 0

    @property
    def top_score(self) -> float | None:
        return self.retrieval_scores[0] if self.retrieval_scores else None

    def __repr__(self) -> str:
        return (
            f"RAGResponse(model={self.model!r}, "
            f"chunks={self.chunks_used}, "
            f"retrieval={self.retrieval_ms:.0f}ms, "
            f"generation={self.generation_ms:.0f}ms)"
        )
