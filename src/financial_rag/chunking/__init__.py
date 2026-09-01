"""Chunking — split Documents into retrievable Chunk objects."""

from financial_rag.chunking.models import Chunk
from financial_rag.chunking.splitter import RecursiveCharacterSplitter

__all__ = ["Chunk", "RecursiveCharacterSplitter"]
