from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pydantic import field_validator, ValidationInfo


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ENV: str
    APP_NAME: str
    DEBUG: bool = False

    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_JWT_SECRET: str

    DATABASE_URL: str

    GROK_API_KEY: str
    GROK_BASE_URL: str

    LANGFUSE_SECRET_KEY: str
    LANGFUSE_PUBLIC_KEY: str
    LANGFUSE_BASE_URL: str | None = None
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"

    ELEVENLABS_API_KEY: str
    N8N_ORDER_WEBHOOK: str
    RAZORPAY_KEY_ID: str
    RAZORPAY_KEY_SECRET: str

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if isinstance(value, str) and value.startswith("DATABASE_URL="):
            return value.split("=", 1)[1]
        return value

    @field_validator("DEBUG", mode="before")
    @classmethod
    def normalize_debug(cls, value):
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on", "debug", "dev", "development"}:
                return True
            if normalized in {"0", "false", "no", "off", "release", "prod", "production"}:
                return False
        return value

    @field_validator("LANGFUSE_HOST", mode="before")
    @classmethod
    def normalize_langfuse_host(cls, value: str | None, info: ValidationInfo) -> str:
        if isinstance(value, str) and value.startswith("LANGFUSE_HOST="):
            value = value.split("=", 1)[1]

        if isinstance(value, str) and value.strip():
            return value.strip()

        base_url = info.data.get("LANGFUSE_BASE_URL")
        if isinstance(base_url, str) and base_url.strip():
            return base_url.strip()

        return "https://cloud.langfuse.com"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
