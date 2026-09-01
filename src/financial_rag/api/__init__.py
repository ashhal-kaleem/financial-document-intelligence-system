"""API — FastAPI application exposing the RAG pipeline over HTTP."""

from financial_rag.api.app import create_app

__all__ = ["create_app"]
