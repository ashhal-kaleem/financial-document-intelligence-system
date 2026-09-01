"""Abstract base class for all document loaders."""

from abc import ABC, abstractmethod
from pathlib import Path

from financial_rag.ingestion.models import Document


class BaseLoader(ABC):
    """Contract that every loader must fulfill.

    Implement this to add support for a new document source
    (Word, HTML, S3, database) without changing any downstream code.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        if not self.path.exists():
            raise FileNotFoundError(f"File not found: {self.path}")

    @abstractmethod
    def load(self) -> list[Document]:
        """Load the file and return a list of Document objects.

        One Document per logical unit (e.g. one per page for PDFs,
        one per file for plain text).
        """
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(path={self.path.name!r})"
