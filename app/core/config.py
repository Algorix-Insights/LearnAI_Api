from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "LearnIA API"
    app_version: str = "0.1.0"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    supabase_url: str | None = None
    supabase_secret_key: str | None = None
    openrouter_api_key: str | None = None
    openrouter_http_referer: str | None = None
    openrouter_app_title: str = "LearnIA API"
    openrouter_app_categories: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
