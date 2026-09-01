"""Document ingestion — load and parse raw files into Document objects."""

from financial_rag.ingestion.factory import load_directory, load_document
from financial_rag.ingestion.models import Document

__all__ = ["Document", "load_document", "load_directory"]
