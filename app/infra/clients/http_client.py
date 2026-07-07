from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import httpx

JsonBody = Mapping[str, Any] | list[Any] | str | int | float | bool | None
Headers = Mapping[str, str]
QueryParams = Mapping[str, str | int | float | bool | None]


@dataclass(frozen=True)
class HttpResponse:
    status_code: int
    data: Any
    headers: dict[str, str]


class HttpClientError(Exception):
    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        data: Any = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.data = data


class HttpClient:
    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 10.0,
        headers: Headers | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._headers = dict(headers or {})
        self._transport = transport

    async def get(
        self,
        path: str,
        *,
        params: QueryParams | None = None,
        headers: Headers | None = None,
    ) -> HttpResponse:
        return await self.request("GET", path, params=params, headers=headers)

    async def post(
        self,
        path: str,
        *,
        json: JsonBody = None,
        params: QueryParams | None = None,
        headers: Headers | None = None,
    ) -> HttpResponse:
        return await self.request("POST", path, json=json, params=params, headers=headers)

    async def put(
        self,
        path: str,
        *,
        json: JsonBody = None,
        params: QueryParams | None = None,
        headers: Headers | None = None,
    ) -> HttpResponse:
        return await self.request("PUT", path, json=json, params=params, headers=headers)

    async def patch(
        self,
        path: str,
        *,
        json: JsonBody = None,
        params: QueryParams | None = None,
        headers: Headers | None = None,
    ) -> HttpResponse:
        return await self.request("PATCH", path, json=json, params=params, headers=headers)

    async def delete(
        self,
        path: str,
        *,
        params: QueryParams | None = None,
        headers: Headers | None = None,
    ) -> HttpResponse:
        return await self.request("DELETE", path, params=params, headers=headers)

    async def request(
        self,
        method: str,
        path: str,
        *,
        json: JsonBody = None,
        params: QueryParams | None = None,
        headers: Headers | None = None,
    ) -> HttpResponse:
        request_headers = {**self._headers, **dict(headers or {})}

        try:
            async with httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout,
                headers=request_headers,
                transport=self._transport,
            ) as client:
                request_kwargs: dict[str, Any] = {
                    "method": method,
                    "url": self._normalize_path(path),
                    "params": self._clean_params(params),
                }
                if json is not None:
                    request_kwargs["json"] = json

                response = await client.request(**request_kwargs)
        except httpx.TimeoutException as exc:
            raise HttpClientError("HTTP request timed out") from exc
        except httpx.RequestError as exc:
            raise HttpClientError(f"HTTP request failed: {exc}") from exc

        data = self._parse_response(response)

        if response.is_error:
            raise HttpClientError(
                "HTTP response returned an error",
                status_code=response.status_code,
                data=data,
            )

        return HttpResponse(
            status_code=response.status_code,
            data=data,
            headers=dict(response.headers),
        )

    def _normalize_path(self, path: str) -> str:
        return path if path.startswith("/") else f"/{path}"

    def _clean_params(self, params: QueryParams | None) -> dict[str, str | int | float | bool]:
        if params is None:
            return {}

        return {key: value for key, value in params.items() if value is not None}

    def _parse_response(self, response: httpx.Response) -> Any:
        if not response.content:
            return None

        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            return response.json()

        return response.text
