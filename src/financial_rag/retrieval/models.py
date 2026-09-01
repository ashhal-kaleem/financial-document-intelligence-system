"""Data model for a retrieval result."""

from dataclasses import dataclass

from financial_rag.retrieval.vector_store import SearchResult


@dataclass
class RetrievalResult:
    """The output of a single retrieval call.

    Wraps ranked SearchResult objects together with the original query so
    downstream components (generator, evaluator, UI) have full context without
    needing to pass query and results separately.
    """

    query: str
    results: list[SearchResult]

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def is_empty(self) -> bool:
        return self.total == 0

    @property
    def top(self) -> SearchResult | None:
        """Highest-ranked result, or None if empty."""
        return self.results[0] if self.results else None

    @property
    def citations(self) -> list[str]:
        """Human-readable source references for every result."""
        return [r.citation for r in self.results]

    def __repr__(self) -> str:
        top_score = f"{self.top.score:.3f}" if self.top else "N/A"
        return (
            f"RetrievalResult(query={self.query!r}, "
            f"total={self.total}, top_score={top_score})"
        )
