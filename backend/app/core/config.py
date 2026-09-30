"""
ResearchMind — Application Configuration
All settings are loaded from environment variables / .env file.
Never hard-code secrets here.
"""
from __future__ import annotations

import secrets
from typing import Any, List, Optional

from pydantic import AnyHttpUrl, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ───────────────────────────
    APP_NAME: str = "ResearchMind"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # ── Security ──────────────────────────────
    SECRET_KEY: str = secrets.token_urlsafe(64)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Database ──────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://researchmind:researchmind_secret@localhost:5432/researchmind"
    DATABASE_URL_SYNC: str = "postgresql+psycopg2://researchmind:researchmind_secret@localhost:5432/researchmind"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30

    # ── Redis ─────────────────────────────────
    REDIS_URL: str = "redis://:redis_secret@localhost:6379/0"

    # ── CORS ──────────────────────────────────
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # ── File Storage ──────────────────────────
    UPLOAD_DIR: str = "/app/uploads"
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_UPLOAD_EXTENSIONS: List[str] = ["pdf", "txt"]

    @field_validator("ALLOWED_UPLOAD_EXTENSIONS", mode="before")
    @classmethod
    def parse_extensions(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(",")]
        return v

    # ── NLP ───────────────────────────────────
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_DIMENSION: int = 384
    SPACY_MODEL: str = "en_core_web_sm"

    # ── LLM Provider ──────────────────────────
    LLM_PROVIDER: str = "demo"  # demo | openai | gemini | local

    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"

    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # ── External Academic APIs ─────────────────
    SEMANTIC_SCHOLAR_API_KEY: Optional[str] = None
    OPENALEX_EMAIL: Optional[str] = None

    # ── Rate Limiting ─────────────────────────
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 10

    # ── Logging ───────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # ── Worker ────────────────────────────────
    WORKER_CONCURRENCY: int = 4
    JOB_TIMEOUT_SECONDS: int = 3600
    JOB_MAX_RETRIES: int = 3

    # ── Retrieval ─────────────────────────────
    DEFAULT_TOP_K: int = 10
    BM25_TOP_K: int = 20
    DENSE_TOP_K: int = 20
    RERANK_TOP_K: int = 10
    HYBRID_ALPHA: float = 0.5  # 0 = BM25 only, 1 = dense only

    @model_validator(mode="after")
    def validate_settings(self) -> "Settings":
        if self.ENVIRONMENT == "production" and self.DEBUG:
            raise ValueError("DEBUG must be False in production")
        return self

    @property
    def is_demo_mode(self) -> bool:
        return self.LLM_PROVIDER == "demo"

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024


# Singleton instance
settings = Settings()
