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

    # Answer generation (server-side, free Groq plan; key stays on the server)
    GROQ_API_KEY: str = Field("", description="Groq API key for server-side answers (free plan)")
    GROQ_MODEL: str = Field("openai/gpt-oss-120b", description="Configured Groq model; no caller override")
    GROQ_TIMEOUT_SECONDS: float = Field(60.0, ge=5, le=120)
    LLM_MAX_OUTPUT_TOKENS: int = Field(1024, ge=1, le=8192)

    # Guest-session and free-quota guards (public no-login deployment)
    GUEST_DAILY_QUESTION_LIMIT: int = Field(20, ge=1, description="Per-guest free answers per UTC day")
    GLOBAL_DAILY_ANSWER_LIMIT: int = Field(60, ge=1, description="All guests combined; token-aware margin under the Groq free plan's daily token cap")
    GUEST_MAX_DOCUMENTS: int = Field(5, ge=1, description="Live documents per guest at a time")
    GUEST_DATA_TTL_HOURS: int = Field(24, ge=1, description="Anonymous guest uploads auto-delete after this many hours")
    CRON_SECRET: str = Field("", description="Bearer secret Vercel Cron sends to the scheduled sweep endpoint")

    # Transactional Email Configuration
    RESEND_API_KEY: str = Field("", description="Resend Email API Key")

    # Embedding & RAG Parameters
    MAX_DOCUMENT_CHUNKS: int = Field(2000, ge=1, le=5000, description="Bound CPU/memory work per report")
    PDF_PARSE_TIMEOUT_SECONDS: float = Field(45.0, ge=1, le=90)
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
    UPLOAD_ABANDON_SECONDS: int = Field(6 * 3600, description="Inline sweep: uploaded rows (never ingested) older than this are reclaimed; must exceed the signed-upload URL lifetime")
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
