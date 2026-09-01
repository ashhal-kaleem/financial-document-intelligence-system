"""Application-wide configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All configuration is read from environment variables or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM — Groq API
    llm_backend: str = "mock"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    # Embeddings
    embedding_model: str = "all-MiniLM-L6-v2"

    # Vector store — "faiss" | "supabase"
    vector_store: str = "faiss"
    vector_store_path: str = "data/processed/vector_store"

    # Supabase (required only when vector_store = "supabase")
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_table: str = "chunks"
    supabase_rpc: str = "match_chunks"

    # Chunking
    chunk_size: int = 512
    chunk_overlap: int = 64

    # Retrieval
    retrieval_top_k: int = 5
    retrieval_score_threshold: float = 0.3
    use_reranker: bool = False
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    reranker_candidates: int = 20

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True
    # Comma-separated list of allowed CORS origins
    cors_origins: str = "http://localhost:3000"

    # Logging
    log_level: str = "INFO"


settings = Settings()
