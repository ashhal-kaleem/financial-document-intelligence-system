"""Data model for a text chunk produced by the splitter."""

from dataclasses import dataclass, field
from financial_rag.ingestion.models import Document


@dataclass
class Chunk:
    """A contiguous slice of a Document, ready for embedding.

    Every Chunk retains full provenance: which file it came from,
    which page, and its position among siblings. This is what makes
    citations possible — the answer cites the Chunk, and the Chunk
    knows exactly where it lives in the source document.
    """

    content: str
    source: str          # inherited from parent Document
    page: int            # page number in the original file
    chunk_index: int     # position among sibling chunks (0-indexed)
    total_chunks: int    # how many chunks this Document produced
    metadata: dict = field(default_factory=dict)

    @classmethod
    def from_document(
        cls,
        document: Document,
        content: str,
        chunk_index: int,
        total_chunks: int,
    ) -> "Chunk":
        """Create a Chunk from a parent Document."""
        filename = document.source.split('/')[-1].split('\\')[-1]
        content_with_context = f"Document: {filename}\n{content}"
        return cls(
            content=content_with_context,
            source=document.source,
            page=document.page,
            chunk_index=chunk_index,
            total_chunks=total_chunks,
            metadata={**document.metadata, "chunk_index": chunk_index},
        )

    @property
    def char_count(self) -> int:
        return len(self.content)

    @property
    def filename(self) -> str:
        from pathlib import Path
        return Path(self.source).name

    @property
    def citation(self) -> str:
        """Human-readable source reference for citations."""
        return f"{self.filename}, p.{self.page + 1} (chunk {self.chunk_index + 1}/{self.total_chunks})"

    def __repr__(self) -> str:
        preview = self.content[:60].replace("\n", " ")
        return (
            f"Chunk(source={self.filename!r}, page={self.page}, "
            f"idx={self.chunk_index}/{self.total_chunks}, "
            f"chars={self.char_count}, preview={preview!r})"
        )
