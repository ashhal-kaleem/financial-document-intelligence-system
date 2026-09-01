"""Retrieval — vector store and semantic search over chunk embeddings."""

from financial_rag.retrieval.vector_store import FAISSVectorStore, SearchResult
from financial_rag.retrieval.supabase_vector_store import SupabaseVectorStore
from financial_rag.retrieval.base import BaseRetriever
from financial_rag.retrieval.models import RetrievalResult
from financial_rag.retrieval.retriever import VectorRetriever
from financial_rag.retrieval.factory import create_retriever

__all__ = [
    "FAISSVectorStore",
    "SupabaseVectorStore",
    "SearchResult",
    "BaseRetriever",
    "RetrievalResult",
    "VectorRetriever",
    "create_retriever",
]
