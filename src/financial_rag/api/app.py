"""FastAPI application factory."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from financial_rag.api.routes import router
from financial_rag.config import settings

_DEFAULT_STORE = "data/processed/vector_store"
_DEFAULT_MODEL = "llama-3.1-8b-instant"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Build the RAG pipeline once at startup; tear down on shutdown.

    If app.state.pipeline is already set (e.g. injected in tests),
    skip creation so tests can supply their own mock.

    The vector-store backend is determined by *app.state.backend*
    (defaults to ``"faiss"``).  When ``"supabase"``, Supabase credentials
    are read from *app.state* (populated by :func:`create_app` from
    :data:`financial_rag.config.settings`).
    """
    if app.state.pipeline is None:
        store_path = getattr(app.state, "store_path", _DEFAULT_STORE)
        model = getattr(app.state, "model", _DEFAULT_MODEL)
        backend = getattr(app.state, "backend", "faiss")
        supabase_url = getattr(app.state, "supabase_url", "")
        supabase_key = getattr(app.state, "supabase_key", "")
        supabase_table = getattr(app.state, "supabase_table", "chunks")
        supabase_rpc = getattr(app.state, "supabase_rpc", "match_chunks")

        from financial_rag.pipeline.factory import create_pipeline
        app.state.pipeline = create_pipeline(
            store_path=store_path,
            model=model,
            api_key=settings.groq_api_key,
            use_reranker=settings.use_reranker,
            reranker_model=settings.reranker_model,
            reranker_candidates=settings.reranker_candidates,
            backend=backend,
            supabase_url=supabase_url,
            supabase_key=supabase_key,
            supabase_table=supabase_table,
            supabase_rpc=supabase_rpc,
        )
        print(
            f"  [api] Pipeline ready — model={model}, "
            f"backend={backend}, store={store_path}"
        )
    yield
    app.state.pipeline = None
    print("  [api] Pipeline shut down.")


def create_app(
    store_path: str = _DEFAULT_STORE,
    model: str = _DEFAULT_MODEL,
    cors_origins: list[str] | None = None,
    backend: str | None = None,
) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        store_path: Path to the FAISS index (without extension).
            Ignored when the active backend is ``"supabase"``.
        model: Groq model tag for generation.
        cors_origins: Allowed CORS origins.  Reads from settings when None.
        backend: Vector-store backend — ``"faiss"`` or ``"supabase"``.
            Reads ``settings.vector_store`` when None (default ``"faiss"``).

    Returns:
        Configured FastAPI app ready to serve.
    """
    app = FastAPI(
        title="Financial RAG Assistant",
        description="RAG API for Peruvian bank annual reports.",
        version="0.1.0",
        lifespan=lifespan,
    )

    resolved_backend = backend if backend is not None else settings.vector_store

    # Store config so lifespan can read it
    app.state.store_path = store_path
    app.state.model = model
    app.state.pipeline = None
    app.state.backend = resolved_backend
    app.state.supabase_url = settings.supabase_url
    app.state.supabase_key = settings.supabase_key
    app.state.supabase_table = settings.supabase_table
    app.state.supabase_rpc = settings.supabase_rpc

    origins = cors_origins or [o.strip() for o in settings.cors_origins.split(",")]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)
    return app


app = create_app()
