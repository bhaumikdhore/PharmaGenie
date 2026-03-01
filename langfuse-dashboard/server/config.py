"""
Observability Server – Central Configuration
All settings are read from environment variables (or .env at project root).
"""
from __future__ import annotations
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Langfuse ──────────────────────────────────────────────────────────────
    langfuse_public_key: str = "pk-lf-pharmagenie-public"
    langfuse_secret_key: str = "sk-lf-pharmagenie-secret"
    langfuse_host: str = "http://localhost:3100"

    # ── LLM ──────────────────────────────────────────────────────────────────
    openai_api_key: str = ""
    default_llm_model: str = "gpt-4o-mini"

    # ── Redis (optional — leave empty to disable) ────────────────────────────
    redis_url: str = ""

    # ── PharmaGenie backend ───────────────────────────────────────────────────
    pharmagenie_backend_url: str = "http://localhost:8000"

    # ── Server ────────────────────────────────────────────────────────────────
    obs_server_host: str = "0.0.0.0"
    obs_server_port: int = 8001
    debug: bool = False

    # ── Application meta ──────────────────────────────────────────────────────
    app_name: str = "PharmaGenie Observability"
    app_version: str = "1.0.0"


@lru_cache
def get_settings() -> Settings:
    return Settings()
