"""Abstract base class for all retriever backends."""

from abc import ABC, abstractmethod

from financial_rag.retrieval.models import RetrievalResult


class BaseRetriever(ABC):
    """Contract for retrieval components.

    A retriever takes a natural language query and returns ranked chunks.
    Swap implementations (vector, BM25, hybrid) without changing the rest
    of the pipeline.
    """

    @abstractmethod
    def retrieve(self, query: str, top_k: int = 5) -> RetrievalResult:
        """Find the most relevant chunks for a query.

        Args:
            query: Natural language question.
            top_k: Maximum number of results to return.

        Returns:
            RetrievalResult with ranked chunks and provenance.
        """
        ...
