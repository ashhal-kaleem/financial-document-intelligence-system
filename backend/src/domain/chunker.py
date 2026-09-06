import re
from typing import List, Tuple
from uuid import UUID
from src.domain.models import DocumentChunk


class RecursiveFinancialChunker:
    """
    Recursive chunker designed specifically for corporate financial reports:
    - Target chunk size: ~512 characters (balanced for dense MiniLM embeddings)
    - Overlap: ~64 characters (preserves sentence continuity across chunks)
    - Preserves balance sheet row/column structure and tables
    """

    def __init__(self, target_chunk_size: int = 512, overlap: int = 64):
        self.target_chunk_size = target_chunk_size
        self.overlap = overlap
        self.separators = ["\n\n", "\n", ". ", "; ", ", ", " "]

    def _split_text_recursively(self, text: str, separators: List[str]) -> List[str]:
        if not separators or len(text) <= self.target_chunk_size:
            return [text.strip()] if text.strip() else []

        sep = separators[0]
        splits = text.split(sep)
        chunks: List[str] = []
        current_chunk = ""

        for piece in splits:
            if not piece.strip():
                continue
            
            # If a single piece is itself too large, recurse with finer separators
            if len(piece) > self.target_chunk_size and len(separators) > 1:
                sub_chunks = self._split_text_recursively(piece, separators[1:])
                for sub in sub_chunks:
                    if len(current_chunk) + len(sub) + len(sep) <= self.target_chunk_size:
                        current_chunk = (current_chunk + sep + sub).strip() if current_chunk else sub
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = sub
                continue

            if len(current_chunk) + len(piece) + len(sep) <= self.target_chunk_size:
                current_chunk = (current_chunk + sep + piece).strip() if current_chunk else piece
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = piece

        if current_chunk:
            chunks.append(current_chunk)

        # Apply overlap between consecutive chunks if applicable
        if self.overlap > 0 and len(chunks) > 1:
            overlapped_chunks = []
            for i in range(len(chunks)):
                if i == 0:
                    overlapped_chunks.append(chunks[i])
                else:
                    prev_tail = chunks[i - 1][-self.overlap:]
                    # Ensure we don't duplicate identical text
                    if not chunks[i].startswith(prev_tail):
                        overlapped_chunks.append(prev_tail + " ... " + chunks[i])
                    else:
                        overlapped_chunks.append(chunks[i])
            return overlapped_chunks

        return chunks

    def chunk_page(
        self,
        document_id: UUID,
        source: str,
        page_number: int,
        page_text: str,
        page_tables: List[str] = None,
    ) -> List[DocumentChunk]:
        """
        Chunks a single page's text and table content.
        Preserves table formatting at the start of chunks.
        """
        combined_text_parts = []
        if page_tables:
            for table_str in page_tables:
                if table_str.strip():
                    combined_text_parts.append(f"--- [Table on Page {page_number}] ---\n{table_str.strip()}")

        if page_text.strip():
            combined_text_parts.append(page_text.strip())

        full_page_content = "\n\n".join(combined_text_parts)
        if not full_page_content.strip():
            return []

        raw_chunks = self._split_text_recursively(full_page_content, self.separators)
        
        doc_chunks = []
        for idx, chunk_text in enumerate(raw_chunks):
            doc_chunks.append(
                DocumentChunk(
                    document_id=document_id,
                    content=chunk_text,
                    source=source,
                    page=page_number,
                    chunk_index=idx,
                    total_chunks=len(raw_chunks),
                    metadata={"page": page_number, "has_table": bool(page_tables)},
                )
            )
        return doc_chunks
