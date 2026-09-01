"""ASGI entry point for production: uvicorn financial_rag.api.asgi:app

Provides a stable module-level ``app`` object so uvicorn / gunicorn can
reference it directly without touching the application factory.
"""

from financial_rag.api.app import create_app
from financial_rag.config import settings

app = create_app(
    store_path=settings.vector_store_path,
    model=settings.groq_model,
)
