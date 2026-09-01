"""Loader for plain text (.txt) files."""

from pathlib import Path

from financial_rag.ingestion.base import BaseLoader
from financial_rag.ingestion.models import Document


class TextLoader(BaseLoader):
    """Loads a plain text file as a single Document."""

    def __init__(self, path: str | Path, encoding: str = "utf-8") -> None:
        super().__init__(path)
        self.encoding = encoding

    def load(self) -> list[Document]:
        text = self.path.read_text(encoding=self.encoding)
        return [
            Document(
                content=text,
                source=self.path.name,
                page=0,
                metadata={
                    "filename": self.path.name,
                    "extension": self.path.suffix,
                    "size_bytes": self.path.stat().st_size,
                },
            )
        ]
