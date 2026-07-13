from functools import lru_cache

from supabase import Client, create_client
from supabase.client import ClientOptions

from app.core.config import get_settings


@lru_cache
def get_supabase_admin_client() -> Client:
    """Return the process-wide service client.

    This client must never execute end-user authentication methods. Supabase auth
    events mutate the client's Authorization header, so mixing sign-in calls with
    service-role data access can leak one request's auth context into another.
    """
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_secret_key:
        raise RuntimeError("Faltan SUPABASE_URL o SUPABASE_SECRET_KEY.")
    return create_client(
        settings.supabase_url,
        settings.supabase_secret_key,
        options=ClientOptions(
            auto_refresh_token=False,
            persist_session=False,
            postgrest_client_timeout=10,
            storage_client_timeout=10,
            schema="public",
        ),
    )


def get_supabase_auth_client() -> Client:
    """Build an isolated, non-persistent Auth client for one API request."""
    settings = get_settings()
    auth_key = settings.supabase_publishable_key or settings.supabase_secret_key
    if not settings.supabase_url or not auth_key:
        raise RuntimeError(
            "Faltan SUPABASE_URL o SUPABASE_PUBLISHABLE_KEY (o SUPABASE_SECRET_KEY) para autenticación."
        )
    return create_client(
        settings.supabase_url,
        auth_key,
        options=ClientOptions(
            auto_refresh_token=False,
            persist_session=False,
            postgrest_client_timeout=10,
            storage_client_timeout=10,
            schema="public",
        ),
    )


def create_supabase_user_client(jwt_token: str) -> Client:
    """Create a request-scoped data client whose RLS identity is the user JWT."""
    if not jwt_token:
        raise ValueError("Se requiere un JWT de usuario.")
    settings = get_settings()
    auth_key = settings.supabase_publishable_key or settings.supabase_secret_key
    if not settings.supabase_url or not auth_key:
        raise RuntimeError(
            "Faltan SUPABASE_URL o SUPABASE_PUBLISHABLE_KEY (o SUPABASE_SECRET_KEY) para acceso de usuario."
        )
    return create_client(
        settings.supabase_url,
        auth_key,
        options=ClientOptions(
            headers={"Authorization": f"Bearer {jwt_token}"},
            auto_refresh_token=False,
            persist_session=False,
            postgrest_client_timeout=10,
            storage_client_timeout=10,
            schema="public",
        ),
    )
