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
    cors_allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    supabase_url: str | None = None
    supabase_publishable_key: str | None = None
    supabase_secret_key: str | None = None
    auth_recovery_redirect_url: str | None = None
    auth_rate_limit_enabled: bool = False
    ai_usage_quota_enabled: bool = False
    openrouter_api_key: str | None = None
    openrouter_http_referer: str | None = None
    openrouter_app_title: str = "LearnIA API"
    openrouter_app_categories: str | None = None
    openrouter_chat_model: str = "openai/gpt-5.2"
    openrouter_embedding_model: str = "openai/text-embedding-3-small"
    documents_bucket: str = "documents"
    profile_bucket: str = "profile"
    rag_match_limit: int = 6
    max_request_body_bytes: int = 12 * 1024 * 1024

    @property
    def cors_origins(self) -> list[str]:
        """Return normalized, unique browser origins configured as CSV."""
        return list(
            dict.fromkeys(
                origin.strip().rstrip("/")
                for origin in self.cors_allowed_origins.split(",")
                if origin.strip()
            )
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
