from functools import lru_cache

from supabase import Client, create_client
from supabase.client import ClientOptions

from app.core.config import get_settings


@lru_cache
def get_supabase_client() -> Client:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_secret_key:
        raise RuntimeError("Faltan SUPABASE_URL o SUPABASE_SECRET_KEY.")
    return create_client(
        settings.supabase_url,
        settings.supabase_secret_key,
        options=ClientOptions(
            postgrest_client_timeout=10,
            storage_client_timeout=10,
            schema="public",
        ),
    )
