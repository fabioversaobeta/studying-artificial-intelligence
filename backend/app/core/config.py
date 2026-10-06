"""Application configuration, loaded from environment variables.

Centralizing config here (instead of reading os.environ throughout the
codebase) keeps every module testable and makes the full list of required
settings discoverable in one place.
"""

import json
from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

INSECURE_DEFAULT_SECRET_KEY = "dev-secret-key-change-me-in-production"
MIN_SECRET_KEY_LENGTH = 32


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Learning Platform API"
    environment: str = Field(default="development")
    # Safe by default: debug must be opted into explicitly (backend/.env.example
    # sets DEBUG=true for local development only).
    debug: bool = Field(default=False)

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

    secret_key: str = Field(default=INSECURE_DEFAULT_SECRET_KEY)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60  # 1h access token (the client refreshes on 401)
    refresh_token_expire_minutes: int = 60 * 24 * 30  # 30 days refresh token

    # Accepts a JSON array or a comma-separated list in the env var
    # (NoDecode disables pydantic-settings' JSON-only parsing for this field).
    cors_allow_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
    )
    # Only what the API and the frontend actually use, instead of "*".
    cors_allow_methods: list[str] = Field(
        default_factory=lambda: ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    )
    cors_allow_headers: list[str] = Field(
        default_factory=lambda: ["Authorization", "Content-Type", "Accept"]
    )

    @field_validator("cors_allow_origins", mode="before")
    @classmethod
    def _parse_cors_origins(cls, value: object) -> object:
        if isinstance(value, str):
            text = value.strip()
            if text.startswith("["):
                return json.loads(text)
            return [item.strip() for item in text.split(",") if item.strip()]
        return value

    # Rate limiting for /auth/login, /auth/register and /auth/refresh
    # (in-memory, per process, per client IP; login is also limited per e-mail).
    rate_limit_enabled: bool = True
    rate_limit_max_requests: int = Field(default=10, ge=1)
    rate_limit_window_seconds: int = Field(default=60, ge=1)
    # Only enable behind a trusted reverse proxy (e.g. Railway) that sets
    # X-Forwarded-For; otherwise clients could spoof their IP.
    trust_proxy_headers: bool = False

    # Registration policy.
    registration_enabled: bool = True
    # When set, /auth/register requires this code in the request body.
    registration_invite_code: str | None = None

    @model_validator(mode="after")
    def _forbid_insecure_production_config(self) -> "Settings":
        """Refuse to boot in production with a forgeable JWT secret or debug on."""
        if not self.is_production:
            return self
        problems: list[str] = []
        if self.secret_key == INSECURE_DEFAULT_SECRET_KEY:
            problems.append("SECRET_KEY is the insecure development default")
        elif len(self.secret_key) < MIN_SECRET_KEY_LENGTH:
            problems.append(f"SECRET_KEY is shorter than {MIN_SECRET_KEY_LENGTH} characters")
        if self.debug:
            problems.append("DEBUG must be false")
        if "*" in self.cors_allow_origins:
            problems.append("CORS_ALLOW_ORIGINS must list explicit origins, not '*'")
        if problems:
            raise ValueError("Insecure production configuration: " + "; ".join(problems))
        return self

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor; import this instead of instantiating Settings directly."""
    return Settings()
