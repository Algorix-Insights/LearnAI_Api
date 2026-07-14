from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_security_headers_and_request_id_are_set() -> None:
    client = TestClient(create_app(Settings(environment="production")))

    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["x-request-id"]
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["strict-transport-security"].startswith("max-age=")


def test_auth_responses_are_not_cached() -> None:
    client = TestClient(create_app(Settings()))

    response = client.get("/api/v1/auth/not-a-route")

    assert response.status_code == 404
    assert response.headers["cache-control"] == "no-store"


def test_oversized_request_is_rejected_before_route_parsing() -> None:
    client = TestClient(create_app(Settings(max_request_body_bytes=32)))

    response = client.post(
        "/api/v1/auth/otp",
        content=b"x" * 33,
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 413
    assert response.json()["detail"].startswith("El cuerpo")


def test_cors_preflight_allows_local_frontend_to_register() -> None:
    client = TestClient(create_app(Settings()))

    response = client.options(
        "/api/v1/auth/register",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert response.headers["access-control-allow-credentials"] == "true"
    assert "POST" in response.headers["access-control-allow-methods"]


def test_cors_headers_are_present_on_auth_route_errors() -> None:
    client = TestClient(create_app(Settings()))

    response = client.post(
        "/api/v1/auth/register",
        json={},
        headers={"Origin": "http://localhost:3000"},
    )

    assert response.status_code == 422
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    exposed_headers = {
        header.strip().lower()
        for header in response.headers["access-control-expose-headers"].split(",")
    }
    assert exposed_headers == {"x-request-id", "retry-after"}


def test_cors_does_not_allow_an_unknown_origin() -> None:
    client = TestClient(create_app(Settings()))

    response = client.options(
        "/api/v1/auth/register",
        headers={
            "Origin": "https://malicious.example",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_cors_origins_are_normalized_and_deduplicated() -> None:
    settings = Settings(
        cors_allowed_origins=("http://localhost:3000/, http://127.0.0.1:3000,http://localhost:3000")
    )

    assert settings.cors_origins == [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
