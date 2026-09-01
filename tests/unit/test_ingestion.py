"""Unit tests for the ingestion layer."""

import pytest
from pathlib import Path

from financial_rag.ingestion.models import Document
from financial_rag.ingestion.text_loader import TextLoader
from financial_rag.ingestion.factory import load_document, load_directory


SAMPLES_DIR = Path("data/samples")


class TestDocument:
    def test_basic_creation(self):
        doc = Document(content="Hello world", source="test.txt")
        assert doc.content == "Hello world"
        assert doc.source == "test.txt"
        assert doc.page == 0

    def test_char_count(self):
        doc = Document(content="Hello", source="test.txt")
        assert doc.char_count == 5

    def test_filename_property(self):
        doc = Document(content="text", source="/some/path/report.pdf")
        assert doc.filename == "report.pdf"

    def test_empty_content_raises(self):
        with pytest.raises(ValueError, match="empty content"):
            Document(content="   ", source="test.txt")

    def test_metadata_defaults_to_empty_dict(self):
        doc = Document(content="text", source="test.txt")
        assert doc.metadata == {}

    def test_repr(self):
        doc = Document(content="Hello world", source="test.txt")
        assert "test.txt" in repr(doc)


class TestTextLoader:
    def test_load_sample_file(self):
        path = SAMPLES_DIR / "sample_annual_report.txt"
        loader = TextLoader(path)
        docs = loader.load()

        assert len(docs) == 1
        doc = docs[0]
        assert "ACME" in doc.content
        assert doc.page == 0
        assert doc.metadata["extension"] == ".txt"
        assert doc.metadata["size_bytes"] > 0

    def test_source_is_filename_only(self):
        """source must be the bare filename, not an absolute path."""
        path = SAMPLES_DIR / "sample_annual_report.txt"
        loader = TextLoader(path)
        doc = loader.load()[0]
        assert doc.source == "sample_annual_report.txt"
        assert "\\" not in doc.source
        assert "/" not in doc.source

    def test_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            TextLoader("nonexistent/file.txt")


class TestFactory:
    def test_load_txt_file(self):
        path = SAMPLES_DIR / "sample_annual_report.txt"
        docs = load_document(path)
        assert len(docs) >= 1
        assert all(isinstance(d, Document) for d in docs)

    def test_txt_source_is_filename_only(self):
        """source must be the bare filename, not an absolute path."""
        path = SAMPLES_DIR / "sample_annual_report.txt"
        docs = load_document(path)
        for doc in docs:
            assert doc.source == "sample_annual_report.txt"
            assert "\\" not in doc.source
            assert "/" not in doc.source

    def test_unsupported_extension_raises(self):
        # We need a file that exists but has an unsupported extension
        import tempfile, os
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
            f.write(b"content")
            tmp_path = f.name
        try:
            with pytest.raises(ValueError, match="Unsupported file type"):
                load_document(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_load_directory(self):
        docs = load_directory(SAMPLES_DIR)
        assert len(docs) >= 1
        assert all(isinstance(d, Document) for d in docs)

    def test_load_directory_not_found(self):
        with pytest.raises(NotADirectoryError):
            load_directory("nonexistent/dir")

    def test_documents_have_content(self):
        docs = load_document(SAMPLES_DIR / "sample_annual_report.txt")
        for doc in docs:
            assert len(doc.content.strip()) > 0

    def test_directory_sources_are_filenames_only(self):
        """All docs loaded from a directory must have bare-filename sources."""
        docs = load_directory(SAMPLES_DIR)
        for doc in docs:
            assert "\\" not in doc.source
            assert "/" not in doc.source
