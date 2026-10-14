"""Central application configuration using Pydantic Settings."""

import json
from functools import lru_cache
from typing import Any, Literal
from urllib.parse import urlparse

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ENVIRONMENT: Literal["development", "test", "production"] = "development"
    LOG_LEVEL: str = "INFO"

    # API Configuration
    API_PORT: int = 8000
    API_HOST: str = "0.0.0.0"
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Poker Lab"
    CORS_ORIGINS: list[str] | str = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"]
    )

    # Database Configuration (PostgreSQL default, overridden in test with SQLite async)
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://pokerlab:pokerlab_secret@postgres:5432/pokerlab_dev"
    )
    DATABASE_SYNC_URL: str = Field(
        default="postgresql+psycopg://pokerlab:pokerlab_secret@postgres:5432/pokerlab_dev"
    )
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_RECYCLE: int = 1800

    # Worker Configuration
    WORKER_POLL_INTERVAL_SECONDS: float = 1.0
    WORKER_CONCURRENCY: int = 2
    WORKER_LOCK_TIMEOUT_SECONDS: int = 300
    WORKER_HEARTBEAT_INTERVAL_SECONDS: float = 5.0
    WORKER_STALE_TIMEOUT_SECONDS: float = 30.0

    # Solver Configuration
    SOLVER_BIN_PATH: str = "apps/api/bin/solver"
    SOLVER_SOLUTIONS_DIR: str = "data/solutions"
    SOLVER_MAX_CONCURRENT_SOLVES: int = 2
    SOLVER_MAX_MEMORY_MB: int = 450
    SOLVER_DEFAULT_TIMEOUT_SECONDS: int = 300

    # Trusted Provenance & Security Token (Runtime secret, default None = fail-closed)
    INTERNAL_AUDIT_TOKEN: str | None = None

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        """Support both JSON-encoded array and comma-delimited strings for CORS origins."""
        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("CORS_ORIGINS cannot be empty")
            if v.startswith("["):
                try:
                    parsed = json.loads(v)
                    if not isinstance(parsed, list):
                        raise ValueError("CORS_ORIGINS JSON must be a list of origin strings")
                    v = parsed
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Malformed JSON in CORS_ORIGINS: {exc}") from exc
            else:
                v = [part.strip() for part in v.split(",") if part.strip()]

        if not isinstance(v, list) or len(v) == 0:
            raise ValueError("CORS_ORIGINS must contain at least one valid origin")

        valid_origins: list[str] = []
        for origin in v:
            if not isinstance(origin, str):
                raise ValueError(
                    f"Invalid origin type: expected string, got {type(origin).__name__}"
                )
            cleaned = origin.strip().rstrip("/")
            if not cleaned:
                raise ValueError("Origin cannot be empty string")
            parsed = urlparse(cleaned)
            if parsed.scheme not in ("http", "https"):
                raise ValueError(f"Origin '{cleaned}' must have http:// or https:// scheme")
            if not parsed.netloc:
                raise ValueError(f"Origin '{cleaned}' must specify a valid hostname/port")
            valid_origins.append(cleaned)

        return valid_origins


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
