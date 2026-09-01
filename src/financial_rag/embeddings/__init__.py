"""Embeddings — convert text to dense vectors for semantic search."""

from financial_rag.embeddings.base import BaseEmbedder
from financial_rag.embeddings.mock import MockEmbedder
from financial_rag.embeddings.sentence_transformer import SentenceTransformerEmbedder

__all__ = ["BaseEmbedder", "MockEmbedder", "SentenceTransformerEmbedder"]
