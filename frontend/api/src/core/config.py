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

    # Server Configuration
    PORT: int = Field(8000, description="FastAPI server port")
    HOST: str = Field("0.0.0.0", description="FastAPI server host")
    DEBUG: bool = Field(False, description="Debug mode")
    MAX_UPLOAD_SIZE_BYTES: int = Field(25 * 1024 * 1024, description="Max PDF upload size in bytes")
    ALLOWED_EXTENSIONS: list[str] = Field([".pdf"], description="Allowed document extensions")


@lru_cache()
def get_settings() -> Settings:
    return Settings()
