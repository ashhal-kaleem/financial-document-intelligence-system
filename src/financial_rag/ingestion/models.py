"""Core data models for the ingestion layer."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Document:
    """A single document loaded from a source file.

    This is the unit of data that flows through the entire pipeline.
    Every chunk, embedding, and retrieval result is traceable to a Document.
    """

    content: str
    source: str                          # file path or URL
    page: int = 0                        # page number (0-indexed)
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.content.strip():
            raise ValueError(f"Document from '{self.source}' has empty content.")

    @property
    def char_count(self) -> int:
        return len(self.content)

    @property
    def filename(self) -> str:
        return Path(self.source).name

    def __repr__(self) -> str:
        preview = self.content[:60].replace("\n", " ")
        return f"Document(source={self.filename!r}, page={self.page}, chars={self.char_count}, preview={preview!r})"
