"""
Application configuration.

All settings are loaded from environment variables (see .env.example).
Using pydantic-settings gives us validation + type safety for free.
"""
from functools import lru_cache
from typing import List

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- App ---
    PROJECT_NAME: str = "InternAI"
    ENVIRONMENT: str = "development"  # development | staging | production
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True

    # --- Security ---
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24h
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30d
    ENCRYPTION_KEY: str = "CHANGE_ME_32_BYTE_FERNET_KEY_HERE=="  # for field-level encryption

    # --- CORS ---
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        return v

    # --- Database ---
    DATABASE_URL: str = "postgresql+psycopg://internai:internai@localhost:5432/internai"
    DATABASE_URL_SYNC: str = "postgresql+psycopg://internai:internai@localhost:5432/internai"

    # --- Redis / Celery ---
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # --- Storage ---
    STORAGE_BACKEND: str = "local"  # local | s3 | supabase
    LOCAL_STORAGE_PATH: str = "/app/storage"
    S3_BUCKET_NAME: str = ""
    S3_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""

    # --- Email ---
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "InternAI <noreply@internai.app>"

    # --- Telegram ---
    TELEGRAM_BOT_TOKEN: str = ""

    # --- OAuth ---
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""

    # --- Rate limiting ---
    RATE_LIMIT_PER_MINUTE: int = 60

    # --- Matching engine weights (must sum to ~1.0) ---
    WEIGHT_SKILL_MATCH: float = 0.35
    WEIGHT_EXPERIENCE: float = 0.15
    WEIGHT_CGPA: float = 0.10
    WEIGHT_GRAD_YEAR: float = 0.10
    WEIGHT_LOCATION: float = 0.15
    WEIGHT_RESUME_SIMILARITY: float = 0.15


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
