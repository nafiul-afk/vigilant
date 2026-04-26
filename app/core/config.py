"""
Vigilant — Configuration Management
Uses pydantic-settings to pull from .env with validation and typing.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Application-wide configuration sourced from environment variables."""

    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Application ──────────────────────────────────────────────────────
    APP_NAME: str = "Vigilant"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"

    # ── Database ─────────────────────────────────────────────────────────
    # Set USE_SQLITE=true for zero-config local dev (no MySQL required)
    USE_SQLITE: bool = True
    # SQLite path (relative to project root)
    SQLITE_PATH: str = "vigilant_dev.db"

    # MySQL settings (used when USE_SQLITE=false)
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_USER: str = "vigilant_user"
    DB_PASSWORD: str = "vigilant_pass"
    DB_NAME: str = "vigilant_db"

    @property
    def DATABASE_URL(self) -> str:
        if self.USE_SQLITE:
            db_path = ROOT_DIR / self.SQLITE_PATH
            return f"sqlite:///{db_path}"
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            "?charset=utf8mb4"
        )

    # ── Session / Auth ───────────────────────────────────────────────────
    SESSION_MAX_AGE: int = 86400  # 24 hours in seconds

    # ── OAuth2 — Google (Prep) ───────────────────────────────────────────
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/auth/google/callback"
    OAUTH_STATE_MAX_AGE: int = 600

    # ── Email / SMTP (Prep) ──────────────────────────────────────────────
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "alerts@vigilant.app"
    SMTP_USE_TLS: bool = True
    SMTP_USE_SSL: bool = False
    SMTP_TIMEOUT: int = 20

    # ── Watcher ──────────────────────────────────────────────────────────
    WATCHER_POLL_INTERVAL: int = 60  # seconds between sweeps
    WATCHER_ALERT_DAYS: int = 3  # alert N days before trial ends

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug_flag(cls, value: object) -> object:
        """Support env values like DEBUG=release without crashing startup."""
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on", "debug", "development", "dev"}:
                return True
            if normalized in {"0", "false", "no", "off", "release", "production", "prod"}:
                return False
        return value

    @property
    def GOOGLE_OAUTH_ENABLED(self) -> bool:
        return bool(
            self.GOOGLE_CLIENT_ID.strip()
            and self.GOOGLE_CLIENT_SECRET.strip()
            and self.GOOGLE_REDIRECT_URI.strip()
        )

    @property
    def SMTP_ENABLED(self) -> bool:
        return bool(
            self.SMTP_HOST.strip()
            and self.SMTP_USER.strip()
            and self.SMTP_PASSWORD.strip()
            and self.EMAIL_FROM.strip()
        )


@lru_cache()
def get_settings() -> Settings:
    """Return a cached singleton of the application settings."""
    return Settings()
