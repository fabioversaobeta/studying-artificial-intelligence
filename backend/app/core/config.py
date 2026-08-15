"""Application configuration, loaded from environment variables.

Centralizing config here (instead of reading os.environ throughout the
codebase) keeps every module testable and makes the full list of required
settings discoverable in one place.
"""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Learning Platform API"
    environment: str = Field(default="development")
    debug: bool = Field(default=True)

    database_url: str = Field(
        default="postgresql+psycopg://learning_platform:learning_platform@localhost:5434/learning_platform"
    )

    @field_validator("database_url")
    @classmethod
    def _normalize_database_url(cls, value: str) -> str:
        """Railway (and Heroku, and most managed-Postgres providers) inject
        DATABASE_URL as `postgresql://...` or `postgres://...`, which
        SQLAlchemy resolves to the psycopg2 dialect. This project uses
        psycopg (v3) instead (see docs/DECISIONS.md), so the scheme must say
        so explicitly — otherwise deploys fail with "no module named
        psycopg2" the first time a request touches the database.
        """
        for prefix in ("postgres://", "postgresql://"):
            if value.startswith(prefix):
                return "postgresql+psycopg://" + value[len(prefix) :]
        return value

    secret_key: str = Field(default="dev-secret-key-change-me-in-production")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24h access token
    refresh_token_expire_minutes: int = 60 * 24 * 30  # 30 days refresh token

    cors_allow_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
    )

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor; import this instead of instantiating Settings directly."""
    return Settings()
