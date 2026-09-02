"""
TalentFlow AI — Centralized Configuration Management
Uses Pydantic BaseSettings with environment validation, structured nested sections,
and fail-fast production checks.
"""
from typing import List, Optional
import os
from pathlib import Path
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Base Directory paths
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
ROOT_DIR = BACKEND_DIR.parent


class DatabaseSettings(BaseSettings):
    """Database connection and pooling configuration."""
    model_config = SettingsConfigDict(env_prefix="DB_", extra="ignore")

    url: str = Field(
        default="",
        alias="DATABASE_URL",
        description="PostgreSQL or SQLite connection string"
    )
    pool_size: int = Field(default=10, description="SQLAlchemy connection pool size")
    max_overflow: int = Field(default=20, description="SQLAlchemy pool max overflow")
    pool_timeout: int = Field(default=30, description="Connection acquisition timeout in seconds")
    pool_recycle: int = Field(default=1800, description="Recycle connections after 30 minutes")
    echo_sql: bool = Field(default=False, description="Log raw SQL queries")


class AuthSettings(BaseSettings):
    """Authentication and JWT token configuration."""
    model_config = SettingsConfigDict(env_prefix="AUTH_", extra="ignore")

    jwt_secret: str = Field(
        default="",
        alias="JWT_SECRET",
        description="Secret key for signing access tokens"
    )
    jwt_refresh_secret: str = Field(
        default="",
        alias="JWT_REFRESH_SECRET",
        description="Secret key for signing refresh tokens"
    )
    flask_secret_key: str = Field(
        default="",
        alias="FLASK_SECRET_KEY",
        description="Flask session secret key"
    )
    admin_secret: str = Field(
        default="",
        alias="ADMIN_SECRET",
        description="Admin API secret header key"
    )
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=60, description="Access token lifetime in minutes")
    refresh_token_expire_days: int = Field(default=7, description="Refresh token lifetime in days")
    bcrypt_rounds: int = Field(default=12, description="Password hashing cost factor")


class RedisSettings(BaseSettings):
    """Redis caching and message broker configuration."""
    model_config = SettingsConfigDict(env_prefix="REDIS_", extra="ignore")

    url: str = Field(
        default="redis://localhost:6379/0",
        alias="REDIS_URL",
        description="Redis connection URL"
    )
    enabled: bool = Field(default=False, alias="REDIS_ENABLED")
    socket_timeout: int = Field(default=5)


class AISettings(BaseSettings):
    """AI engine, HuggingFace, and RAG configuration."""
    model_config = SettingsConfigDict(env_prefix="AI_", extra="ignore")

    hf_token: str = Field(
        default="",
        alias="HF_TOKEN",
        description="HuggingFace API token for inference"
    )
    embedding_model: str = Field(
        default="sentence-transformers/all-mpnet-base-v2",
        alias="EMBEDDING_MODEL"
    )
    llm_model: str = Field(
        default="mistralai/Mistral-7B-Instruct-v0.2",
        alias="LLM_MODEL"
    )
    embedding_cache_max: int = Field(default=500)
    faiss_rebuild_interval: int = Field(default=600, description="FAISS rebuild interval in seconds")


class StorageSettings(BaseSettings):
    """Object and file storage configuration."""
    model_config = SettingsConfigDict(env_prefix="STORAGE_", extra="ignore")

    provider: str = Field(default="local", description="'local' or 's3'")
    local_upload_dir: str = Field(default=str(BACKEND_DIR / "uploads"))
    max_upload_size_mb: int = Field(default=15, alias="MAX_UPLOAD_SIZE_MB")
    allowed_extensions: List[str] = Field(default=["pdf", "docx", "txt"])
    s3_bucket: Optional[str] = Field(default=None, alias="S3_BUCKET")
    s3_endpoint_url: Optional[str] = Field(default=None, alias="S3_ENDPOINT_URL")
    s3_access_key: Optional[str] = Field(default=None, alias="S3_ACCESS_KEY")
    s3_secret_key: Optional[str] = Field(default=None, alias="S3_SECRET_KEY")
    s3_region: str = Field(default="us-east-1", alias="S3_REGION")


class EmailSettings(BaseSettings):
    """Email delivery service configuration."""
    model_config = SettingsConfigDict(env_prefix="EMAIL_", extra="ignore")

    provider: str = Field(default="smtp", description="'smtp', 'sendgrid', 'resend', or 'mock'")
    sender_email: Optional[str] = Field(default=None, alias="SENDER_EMAIL")
    sender_password: Optional[str] = Field(default=None, alias="SENDER_PASSWORD")
    smtp_host: str = Field(default="smtp.gmail.com", alias="SMTP_HOST")
    smtp_port: int = Field(default=465, alias="SMTP_PORT")
    smtp_use_ssl: bool = Field(default=True, alias="SMTP_USE_SSL")


class AppSettings(BaseSettings):
    """Main application configuration aggregating all modular settings."""
    model_config = SettingsConfigDict(
        env_file=(str(BACKEND_DIR / ".env"), str(ROOT_DIR / ".env")),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    app_name: str = "TalentFlow AI"
    environment: str = Field(default="development", alias="FLASK_ENV")
    port: int = Field(default=5000, alias="PORT")
    debug: bool = Field(default=False)
    api_v1_prefix: str = "/api/v1"
    frontend_urls: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173,https://ats917.vercel.app,https://ats-silk-alpha.vercel.app",
        alias="FRONTEND_URLS"
    )
    rate_limit_default: str = Field(default="200 per minute", alias="RATE_LIMIT_DEFAULT")
    rate_limit_auth: str = Field(default="10 per minute", alias="RATE_LIMIT_AUTH")
    rate_limit_ai: str = Field(default="30 per minute", alias="RATE_LIMIT_AI")

    # Sub-settings
    db: DatabaseSettings = Field(default_factory=DatabaseSettings)
    auth: AuthSettings = Field(default_factory=AuthSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    ai: AISettings = Field(default_factory=AISettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    email: EmailSettings = Field(default_factory=EmailSettings)

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in ("production", "prod")

    @property
    def is_development(self) -> bool:
        return self.environment.lower() in ("development", "dev", "local")

    @property
    def is_testing(self) -> bool:
        return self.environment.lower() in ("testing", "test")

    @property
    def cors_origins(self) -> List[str]:
        return [url.strip().rstrip("/") for url in self.frontend_urls.split(",") if url.strip()]

    def validate_production_readiness(self) -> List[str]:
        """Verify strict requirements when deployed in production."""
        issues = []
        if self.is_production:
            if not self.auth.jwt_secret or self.auth.jwt_secret in (
                "dev-secret-change-in-production", "secret", "your-jwt-secret-key-change-in-production", "talentflow-secret-key"
            ):
                issues.append("Production requires a secure, non-default JWT_SECRET.")
            if not self.auth.flask_secret_key or self.auth.flask_secret_key in (
                "talentflow-secret-key", "secret", "change-me"
            ):
                issues.append("Production requires a secure FLASK_SECRET_KEY to be set.")
            if not self.db.url:
                issues.append("Production requires DATABASE_URL to be set to a valid PostgreSQL connection string.")
            elif "sqlite" in self.db.url.lower():
                issues.append("SQLite is not allowed in production. Production requires a PostgreSQL DATABASE_URL.")
            elif not (self.db.url.startswith("postgresql://") or self.db.url.startswith("postgres://")):
                issues.append("Production DATABASE_URL must start with postgresql:// or postgres://.")
        return issues


# Singleton instance
settings = AppSettings()
