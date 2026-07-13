import asyncio
import json
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from supabase_auth.errors import AuthApiError

from app.api import dependencies as api_dependencies
from app.api.auth_rate_limit import InMemoryRateLimiter, RateLimitBucket
from app.core.exceptions import AuthRateLimitError
from app.domain.schemas.resources.auth import (
    AuthForgotPasswordRequest,
    AuthOtpRequest,
    AuthRegisterRequest,
    AuthVerifyOtpRequest,
)
from app.infra.db import supabase as supabase_db
from app.infra.repositories.auth import SupabaseAuthRepository
from app.main import api_error_handler, app


class StubClient:
    def __init__(self, auth: object) -> None:
        self.auth = auth


class RateLimitedAuth:
    def sign_in_with_otp(self, _: dict) -> None:
        raise AuthApiError(
            "email rate limit exceeded: provider-only-detail",
            429,
            "over_email_send_rate_limit",
        )


class CapturingAuth:
    def __init__(self) -> None:
        self.otp_payload: dict | None = None
        self.recovery_call: tuple[str, dict | None] | None = None

    def sign_in_with_otp(self, payload: dict) -> None:
        self.otp_payload = payload

    def reset_password_for_email(self, email: str, options: dict | None = None) -> None:
        self.recovery_call = (email, options)


def test_email_otp_uses_current_type_and_password_minimum() -> None:
    request = AuthVerifyOtpRequest(email="user@example.test", token="123456")
    assert request.type == "email"

    with pytest.raises(ValidationError):
        AuthVerifyOtpRequest(
            email="user@example.test",
            token="123456",
            type="magiclink",
        )

    with pytest.raises(ValidationError):
        AuthRegisterRequest(
            email="user@example.test",
            password="short",
            name="Ada",
            last_name="Lovelace",
        )


def test_provider_rate_limit_is_safe_429_with_retry_header() -> None:
    repository = SupabaseAuthRepository(
        client=StubClient(RateLimitedAuth()),
        recovery_redirect_url="https://app.example.test/auth/reset-password",
    )

    with pytest.raises(AuthRateLimitError) as captured:
        asyncio.run(repository.sign_in_with_otp(AuthOtpRequest(email="user@example.test")))

    error = captured.value
    assert error.status_code == 429
    assert error.headers == {"Retry-After": "60"}
    assert "provider-only-detail" not in error.message

    response = asyncio.run(api_error_handler(None, error))
    assert response.status_code == 429
    assert response.headers["retry-after"] == "60"
    assert "provider-only-detail" not in json.loads(response.body)["detail"]


def test_auth_client_configuration_failure_is_safe_503(monkeypatch) -> None:
    def fail_auth_repository() -> None:
        raise RuntimeError("missing production configuration")

    monkeypatch.setattr(
        api_dependencies,
        "SupabaseAuthRepository",
        fail_auth_repository,
    )

    previous_overrides = dict(app.dependency_overrides)
    app.dependency_overrides.clear()
    try:
        response = TestClient(app).post(
            "/api/v1/auth/login",
            json={"email": "user@example.test", "password": "valid-password"},
        )
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Servicio de autenticación no disponible temporalmente."
    }
    assert "missing production configuration" not in response.text


def test_captcha_is_forwarded_and_recovery_redirect_is_server_controlled() -> None:
    auth = CapturingAuth()
    repository = SupabaseAuthRepository(
        client=StubClient(auth),
        recovery_redirect_url="https://app.example.test/auth/reset-password",
    )

    asyncio.run(
        repository.sign_in_with_otp(
            AuthOtpRequest(
                email="user@example.test",
                captcha_token="captcha-proof",
            )
        )
    )
    assert auth.otp_payload == {
        "email": "user@example.test",
        "options": {
            "should_create_user": False,
            "captcha_token": "captcha-proof",
        },
    }

    asyncio.run(
        repository.reset_password_for_email(
            AuthForgotPasswordRequest(
                email="user@example.test",
                captcha_token="captcha-proof",
            )
        )
    )
    assert auth.recovery_call == (
        "user@example.test",
        {
            "redirect_to": "https://app.example.test/auth/reset-password",
            "captcha_token": "captcha-proof",
        },
    )


def test_supabase_clients_are_isolated_and_non_persistent(monkeypatch) -> None:
    calls: list[tuple[str, str, object]] = []
    settings = SimpleNamespace(
        supabase_url="https://project.example.test",
        supabase_publishable_key="publishable-test-key",
        supabase_secret_key="secret-test-key",
    )

    def fake_create_client(url: str, key: str, options: object) -> object:
        client = object()
        calls.append((url, key, options))
        return client

    supabase_db.get_supabase_admin_client.cache_clear()
    monkeypatch.setattr(supabase_db, "get_settings", lambda: settings)
    monkeypatch.setattr(supabase_db, "create_client", fake_create_client)
    try:
        first_admin = supabase_db.get_supabase_admin_client()
        second_admin = supabase_db.get_supabase_admin_client()
        first_auth = supabase_db.get_supabase_auth_client()
        second_auth = supabase_db.get_supabase_auth_client()
        user_client = supabase_db.create_supabase_user_client("user-jwt")
    finally:
        supabase_db.get_supabase_admin_client.cache_clear()

    assert first_admin is second_admin
    assert first_auth is not second_auth
    assert user_client is not None
    assert len(calls) == 4
    assert calls[0][1] == "secret-test-key"
    assert calls[1][1] == calls[2][1] == calls[3][1] == "publishable-test-key"
    for _, _, options in calls:
        assert options.persist_session is False
        assert options.auto_refresh_token is False
    assert calls[3][2].headers["Authorization"] == "Bearer user-jwt"


def test_in_memory_limiter_is_atomic_and_recovers_after_window() -> None:
    now = [100.0]
    limiter = InMemoryRateLimiter(clock=lambda: now[0])
    bucket = RateLimitBucket("auth:test:ip:local", limit=2, window_seconds=60)

    limiter.enforce([bucket])
    limiter.enforce([bucket])
    with pytest.raises(AuthRateLimitError):
        limiter.enforce([bucket])

    now[0] = 161.0
    limiter.enforce([bucket])


def test_resource_routers_are_default_deny_without_bearer_token() -> None:
    previous_overrides = dict(app.dependency_overrides)
    app.dependency_overrides.clear()
    try:
        response = TestClient(app).get("/api/v1/users")
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)

    assert response.status_code == 401
