import asyncio

import httpx
import pytest

from app.infra.clients import HttpClient, HttpClientError


def run_async(coro):
    return asyncio.run(coro)


def test_http_client_get_sends_headers_params_and_parses_json() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert str(request.url) == "https://api.example.test/users?active=true"
        assert request.headers["authorization"] == "Bearer token"
        return httpx.Response(200, json={"users": []})

    client = HttpClient(
        "https://api.example.test",
        headers={"authorization": "Bearer token"},
        transport=httpx.MockTransport(handler),
    )

    response = run_async(client.get("users", params={"active": "true", "empty": None}))

    assert response.status_code == 200
    assert response.data == {"users": []}


def test_http_client_raises_error_with_status_and_body() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"detail": "not found"})

    client = HttpClient("https://api.example.test", transport=httpx.MockTransport(handler))

    with pytest.raises(HttpClientError) as error:
        run_async(client.get("/missing"))

    assert error.value.status_code == 404
    assert error.value.data == {"detail": "not found"}
