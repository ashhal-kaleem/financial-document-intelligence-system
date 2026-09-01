"""Recursive character text splitter for RAG chunking."""

from financial_rag.ingestion.models import Document
from financial_rag.chunking.models import Chunk


# Separators tried in order — most semantic to least semantic
_DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


class RecursiveCharacterSplitter:
    """Splits documents into overlapping chunks using recursive separator logic.

    Tries to break on paragraph boundaries first, then sentences, then words,
    then raw characters — preserving semantic coherence as much as possible.

    Args:
        chunk_size: Target maximum size of each chunk in characters.
        chunk_overlap: Number of characters to repeat between consecutive chunks.
        separators: Ordered list of separators to try when splitting.
        min_chunk_size: Chunks smaller than this are merged with the next one.
    """

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
        separators: list[str] | None = None,
        min_chunk_size: int = 50,
    ) -> None:
        if chunk_overlap >= chunk_size:
            raise ValueError(
                f"chunk_overlap ({chunk_overlap}) must be less than chunk_size ({chunk_size})"
            )
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or _DEFAULT_SEPARATORS
        self.min_chunk_size = min_chunk_size

    def split_document(self, document: Document) -> list[Chunk]:
        """Split a single Document into a list of Chunks."""
        raw_chunks = self._split_text(document.content)
        total = len(raw_chunks)

        return [
            Chunk.from_document(document, text, idx, total)
            for idx, text in enumerate(raw_chunks)
        ]

    def split_documents(self, documents: list[Document]) -> list[Chunk]:
        """Split a list of Documents into a flat list of Chunks."""
        all_chunks: list[Chunk] = []
        for doc in documents:
            all_chunks.extend(self.split_document(doc))
        return all_chunks

    # ── Internal splitting logic ──────────────────────────────────────────

    def _split_text(self, text: str) -> list[str]:
        """Recursively split text and merge into target-sized chunks."""
        pieces = self._recursive_split(text, self.separators)
        return self._merge_pieces(pieces)

    def _recursive_split(self, text: str, separators: list[str]) -> list[str]:
        """Split text using the first separator that produces manageable pieces."""
        if not separators:
            # No separators left — brute-force character split
            return [text[i : i + self.chunk_size] for i in range(0, len(text), self.chunk_size)]

        separator, *remaining = separators

        if separator == "":
            return [text[i : i + self.chunk_size] for i in range(0, len(text), self.chunk_size)]

        # TABLE HEURISTIC: If splitting by newline, don't split if it's a table (and not absurdly huge)
        if separator == "\n" and len(text) <= 2000 and self._is_table(text):
            return [text]

        parts = text.split(separator)

        result: list[str] = []
        for part in parts:
            part = part.strip()
            if not part:
                continue
            if len(part) <= self.chunk_size:
                result.append(part)
            else:
                # This part is still too large — recurse with next separator
                result.extend(self._recursive_split(part, remaining))

        return result

    def _merge_pieces(self, pieces: list[str]) -> list[str]:
        """Merge small pieces into chunks respecting chunk_size and overlap."""
        if not pieces:
            return []

        chunks: list[str] = []
        current_parts: list[str] = []
        current_size = 0

        for piece in pieces:
            piece_size = len(piece)

            if current_size + piece_size + 1 > self.chunk_size and current_parts:
                # Flush current chunk
                chunk_text = " ".join(current_parts).strip()
                if len(chunk_text) >= self.min_chunk_size:
                    chunks.append(chunk_text)

                # Build overlap: keep trailing parts that fit in overlap window
                overlap_parts: list[str] = []
                overlap_size = 0
                for part in reversed(current_parts):
                    if overlap_size + len(part) + 1 <= self.chunk_overlap:
                        overlap_parts.insert(0, part)
                        overlap_size += len(part) + 1
                    else:
                        break

                current_parts = overlap_parts
                current_size = overlap_size

            current_parts.append(piece)
            current_size += piece_size + 1  # +1 for space separator

        # Flush the last chunk
        if current_parts:
            chunk_text = " ".join(current_parts).strip()
            if len(chunk_text) >= self.min_chunk_size:
                chunks.append(chunk_text)
            elif chunks:
                # Merge tiny tail into the last chunk
                chunks[-1] = chunks[-1] + " " + chunk_text
            else:
                # Only chunk — always include it regardless of min size
                chunks.append(chunk_text)

        return chunks

    def _is_table(self, text: str) -> bool:
        """Detect if a text block is likely a financial table."""
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        if len(lines) < 3:
            return False
        
        data_rows = sum(1 for line in lines if any(char.isdigit() for char in line))
        return (data_rows / len(lines)) >= 0.4
