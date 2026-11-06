from functools import lru_cache
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env.local", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Supabase Configuration
    SUPABASE_URL: str = Field(..., description="Supabase Project API URL")
    SUPABASE_ANON_KEY: str = Field("", description="Supabase Anon/Public Key")
    SUPABASE_SERVICE_ROLE_KEY: str = Field(..., description="Supabase Service Role Key")
    SUPABASE_STORAGE_BUCKET: str = Field("documents", description="Storage bucket name for PDFs")

    # LLM Inference Configuration
    GROQ_API_KEY: str = Field(..., description="Groq LPU API Key")
    GROQ_MODEL: str = Field("qwen/qwen3.8-27b", description="Default Groq model")
    OPENROUTER_API_KEY: str = Field("", description="OpenRouter API Key for fallback")
    OPENROUTER_DEFAULT_MODEL: str = Field("liquid/lfm-2.5-2.6b:free", description="Default OpenRouter fallback model")

    LLM_FALLBACK_ENABLED: bool = False  # opt-in only; a second provider may spend quota/money
    LLM_MAX_OUTPUT_TOKENS: int = Field(1024, ge=1, le=8192)

    # Transactional Email Configuration
    RESEND_API_KEY: str = Field("", description="Resend Email API Key")
    HF_TOKEN: str = Field("", description="Hugging Face API token")

    # Embedding & RAG Parameters
    EMBEDDING_MODEL_NAME: str = Field("all-MiniLM-L6-v2", description="Sentence Transformers model")
    EMBEDDING_DIMENSIONS: int = Field(384, description="Vector dimension size")
    CHUNK_SIZE: int = Field(512, description="Target characters per chunk")
    CHUNK_OVERLAP: int = Field(64, description="Overlap characters between chunks")
    SIMILARITY_THRESHOLD: float = Field(0.05, description="Minimum cosine similarity threshold")
    TOP_K_MATCHES: int = Field(5, description="Number of vector matches to retrieve")

    # Security
    AUTH_REQUIRED: bool = Field(True, description="Set false ONLY for local dev; ignored (fail closed) unless DEBUG=true and not on a hosting platform")
    ALLOWED_ORIGINS: list[str] = Field(["http://localhost:3000"], description="CORS allowed origins (JSON list in env)")
    RATE_LIMIT_PER_MINUTE: int = Field(30, description="Per-user limit for upload and ask endpoints (0 disables)")

    # Server Configuration
    PORT: int = Field(8000, description="FastAPI server port")
    HOST: str = Field("0.0.0.0", description="FastAPI server host")
    DEBUG: bool = Field(False, description="Debug mode")
    MAX_UPLOAD_SIZE_BYTES: int = Field(25 * 1024 * 1024, description="Max PDF upload size in bytes")
    INGESTION_MODE: str = Field("inline", description="inline = process inside the upload request; queue = store, return 202, a background worker processes (needs a long-running host)")
    WORKER_POLL_SECONDS: float = Field(5.0, description="Queue poll interval")
    JOB_STALE_SECONDS: int = Field(600, description="A claimed job older than this is retried")
    JOB_MAX_ATTEMPTS: int = Field(3, description="Attempts before a job is marked error")
    MAX_PDF_PAGES: int = Field(500, description="Reject PDFs with more pages than this")
    ALLOWED_EXTENSIONS: list[str] = Field([".pdf"], description="Allowed document extensions")


def effective_ingestion_mode(settings: "Settings" = None) -> str:
    """queue needs a long-running process. On serverless (Vercel) a queued job would never run, so use inline."""
    import os
    s = settings or get_settings()
    if s.INGESTION_MODE == "queue" and not os.environ.get("VERCEL"):
        return "queue"
    return "inline"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
