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
