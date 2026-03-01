from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = Field(..., alias="DATABASE_URL")
    n8n_low_stock_webhook: str = Field(..., alias="N8N_LOW_STOCK_WEBHOOK")
    webhook_timeout_seconds: float = Field(10.0, alias="WEBHOOK_TIMEOUT_SECONDS")


@lru_cache
def get_settings() -> Settings:
    return Settings()

