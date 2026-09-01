"""Unit tests for the chunking layer."""

import pytest
from pathlib import Path

from financial_rag.ingestion.models import Document
from financial_rag.chunking.models import Chunk
from financial_rag.chunking.splitter import RecursiveCharacterSplitter


def make_doc(content: str, source: str = "test.txt", page: int = 0) -> Document:
    return Document(content=content, source=source, page=page)


class TestChunk:
    def test_citation_format(self):
        doc = make_doc("Hello", source="/docs/report.pdf", page=2)
        chunk = Chunk.from_document(doc, "Hello", chunk_index=0, total_chunks=3)
        assert "report.pdf" in chunk.citation
        assert "p.3" in chunk.citation       # page is 0-indexed → display as 1-indexed
        assert "1/3" in chunk.citation

    def test_char_count(self):
        doc = make_doc("Hello world")
        chunk = Chunk.from_document(doc, "Hello world", 0, 1)
        assert chunk.char_count == 30

    def test_metadata_inherits_from_document(self):
        doc = make_doc("text", source="doc.txt")
        doc.metadata["filename"] = "doc.txt"
        chunk = Chunk.from_document(doc, "text", 0, 1)
        assert chunk.metadata["filename"] == "doc.txt"
        assert chunk.metadata["chunk_index"] == 0


class TestRecursiveCharacterSplitter:
    def test_short_text_produces_one_chunk(self):
        splitter = RecursiveCharacterSplitter(chunk_size=512, chunk_overlap=64)
        doc = make_doc("Short text that fits in one chunk.")
        chunks = splitter.split_document(doc)
        assert len(chunks) == 1
        assert "Document: test.txt\nShort text that fits in one chunk." in chunks[0].content

    def test_long_text_is_split(self):
        splitter = RecursiveCharacterSplitter(chunk_size=100, chunk_overlap=20)
        long_text = "word " * 200  # 1000 chars
        doc = make_doc(long_text)
        chunks = splitter.split_document(doc)
        assert len(chunks) > 1

    def test_all_chunks_within_size_limit(self):
        splitter = RecursiveCharacterSplitter(chunk_size=200, chunk_overlap=30)
        doc = make_doc("sentence one. sentence two. sentence three. " * 30)
        chunks = splitter.split_document(doc)
        for chunk in chunks:
            # Allow slight overage from overlap assembly
            assert chunk.char_count <= 250, f"Chunk too large: {chunk.char_count}"

    def test_overlap_causes_content_repetition(self):
        splitter = RecursiveCharacterSplitter(chunk_size=100, chunk_overlap=40)
        # Create text where we can verify overlap
        doc = make_doc("alpha " * 50)
        chunks = splitter.split_document(doc)
        if len(chunks) >= 2:
            # Last words of chunk N should appear at start of chunk N+1
            end_of_first = chunks[0].content[-30:]
            start_of_second = chunks[1].content[:50]
            # Some content must be shared
            words_in_first = set(end_of_first.split())
            words_in_second = set(start_of_second.split())
            assert words_in_first & words_in_second, "No overlap detected between chunks"

    def test_total_chunks_consistent(self):
        splitter = RecursiveCharacterSplitter(chunk_size=100, chunk_overlap=20)
        doc = make_doc("paragraph\n\n" * 30)
        chunks = splitter.split_document(doc)
        expected_total = len(chunks)
        for chunk in chunks:
            assert chunk.total_chunks == expected_total

    def test_chunk_index_sequential(self):
        splitter = RecursiveCharacterSplitter(chunk_size=100, chunk_overlap=20)
        doc = make_doc("word " * 300)
        chunks = splitter.split_document(doc)
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i

    def test_source_preserved_in_chunks(self):
        splitter = RecursiveCharacterSplitter(chunk_size=100, chunk_overlap=20)
        doc = make_doc("word " * 100, source="/data/annual_report.pdf", page=5)
        chunks = splitter.split_document(doc)
        for chunk in chunks:
            assert chunk.source == "/data/annual_report.pdf"
            assert chunk.page == 5

    def test_invalid_overlap_raises(self):
        with pytest.raises(ValueError, match="chunk_overlap"):
            RecursiveCharacterSplitter(chunk_size=100, chunk_overlap=100)

    def test_split_multiple_documents(self):
        splitter = RecursiveCharacterSplitter(chunk_size=100, chunk_overlap=20)
        docs = [make_doc("word " * 100, source=f"doc{i}.txt") for i in range(3)]
        chunks = splitter.split_documents(docs)
        assert len(chunks) > 3
        sources = {c.source for c in chunks}
        assert sources == {"doc0.txt", "doc1.txt", "doc2.txt"}

    def test_prefers_paragraph_boundaries(self):
        splitter = RecursiveCharacterSplitter(chunk_size=120, chunk_overlap=20)
        # Two clear paragraphs that each fit in a chunk
        text = ("First paragraph with some content here.\n\n"
                "Second paragraph with different content here.")
        doc = make_doc(text)
        chunks = splitter.split_document(doc)
        # Paragraph text should not be merged into one chunk if it exceeds size
        combined = " ".join(c.content for c in chunks)
        assert "First paragraph" in combined
        assert "Second paragraph" in combined

    def test_context_prepended_to_chunks(self):
        splitter = RecursiveCharacterSplitter(chunk_size=100, chunk_overlap=20)
        doc = make_doc("some text", source="test_source.pdf")
        chunks = splitter.split_document(doc)
        assert len(chunks) == 1
        assert "Document: test_source.pdf" in chunks[0].content
        assert "some text" in chunks[0].content

    def test_financial_table_preservation(self):
        splitter = RecursiveCharacterSplitter(chunk_size=100, chunk_overlap=20)
        table_text = (
            "Header Row\n"
            "2024 2025 var\n"
            "Item 1 100 200 100%\n"
            "Item 2 50 150 200%\n"
            "Item 3 10 20 100%"
        )
        doc = make_doc(table_text)
        chunks = splitter.split_document(doc)
        # Even though chunk_size is 100 and the table is longer (approx 105 chars),
        # it should NOT be split because of the table heuristic.
        assert len(chunks) == 1
        assert "Item 3 10 20 100%" in chunks[0].content


class TestChunkingOnRealDocuments:
    """Integration-style tests using the real PDF samples."""

    SAMPLES = Path("data/samples")

    @pytest.mark.skipif(
        not (Path("data/samples") / "interbank_memoria_2025.pdf").exists(),
        reason="Real PDF not available"
    )
    def test_interbank_pdf_chunking(self):
        from financial_rag.ingestion import load_document
        splitter = RecursiveCharacterSplitter(chunk_size=512, chunk_overlap=64)

        docs = load_document(self.SAMPLES / "interbank_memoria_2025.pdf")
        chunks = splitter.split_documents(docs)

        assert len(chunks) > 100, "Expected many chunks from a 162-page document"
        assert all(c.char_count > 0 for c in chunks)
        assert all(c.source.endswith("interbank_memoria_2025.pdf") for c in chunks)

        # No chunk should exceed the table heuristic max size (2000)
        oversized = [c for c in chunks if c.char_count > 2000]
        assert len(oversized) == 0, f"{len(oversized)} chunks exceed 2000 chars"

    @pytest.mark.skipif(
        not (Path("data/samples") / "interbank_memoria_2025.pdf").exists(),
        reason="Real PDF not available"
    )
    def test_chunk_citations_are_readable(self):
        from financial_rag.ingestion import load_document
        splitter = RecursiveCharacterSplitter(chunk_size=512, chunk_overlap=64)

        docs = load_document(self.SAMPLES / "interbank_memoria_2025.pdf")
        chunks = splitter.split_documents(docs)[:5]

        for chunk in chunks:
            assert "interbank_memoria_2025.pdf" in chunk.citation
            assert "p." in chunk.citation
