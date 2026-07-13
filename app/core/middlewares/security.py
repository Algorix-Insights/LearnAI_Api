from __future__ import annotations

import logging
from time import perf_counter
from uuid import uuid4

from fastapi.responses import JSONResponse
from starlette.datastructures import MutableHeaders


logger = logging.getLogger("learnia.http")


class _RequestBodyTooLarge(Exception):
    pass


class SecurityMiddleware:
    """Apply body limits, safe request logs, and baseline security headers."""

    def __init__(
        self,
        app,
        *,
        api_prefix: str = "/api/v1",
        environment: str = "development",
        max_request_body_bytes: int = 12 * 1024 * 1024,
    ) -> None:
        self.app = app
        self.auth_prefix = f"{api_prefix.rstrip('/')}/auth"
        self.is_production = environment.casefold() == "production"
        self.max_request_body_bytes = max_request_body_bytes

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        started_at = perf_counter()
        method = str(scope.get("method", ""))
        path = str(scope.get("path", ""))
        request_id = uuid4().hex
        status_code = 500
        response_started = False
        received_bytes = 0

        async def receive_with_limit():
            nonlocal received_bytes
            message = await receive()
            if message["type"] == "http.request":
                received_bytes += len(message.get("body", b""))
                if received_bytes > self.max_request_body_bytes:
                    raise _RequestBodyTooLarge
            return message

        async def send_with_security_headers(message) -> None:
            nonlocal response_started, status_code
            if message["type"] == "http.response.start":
                response_started = True
                status_code = int(message["status"])
                headers = MutableHeaders(scope=message)
                headers["X-Request-ID"] = request_id
                headers.setdefault("X-Content-Type-Options", "nosniff")
                headers.setdefault("X-Frame-Options", "DENY")
                headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
                headers.setdefault(
                    "Permissions-Policy",
                    "camera=(), microphone=(), geolocation=()",
                )
                if path.startswith(self.auth_prefix):
                    headers.setdefault("Cache-Control", "no-store")
                if self.is_production:
                    headers.setdefault(
                        "Strict-Transport-Security",
                        "max-age=31536000; includeSubDomains",
                    )
            await send(message)

        try:
            content_length = self._content_length(scope)
            if (
                content_length is not None
                and content_length > self.max_request_body_bytes
            ):
                response = JSONResponse(
                    status_code=413,
                    content={"detail": "El cuerpo de la solicitud excede el límite permitido."},
                )
                await response(scope, receive, send_with_security_headers)
                return
            await self.app(scope, receive_with_limit, send_with_security_headers)
        except _RequestBodyTooLarge:
            if response_started:
                raise
            response = JSONResponse(
                status_code=413,
                content={"detail": "El cuerpo de la solicitud excede el límite permitido."},
            )
            await response(scope, receive, send_with_security_headers)
        except Exception:
            logger.exception(
                "http_request_failed method=%s path=%s request_id=%s",
                method,
                path,
                request_id,
            )
            raise
        finally:
            duration_ms = round((perf_counter() - started_at) * 1000, 2)
            logger.info(
                "http_request method=%s path=%s status=%s duration_ms=%s request_id=%s",
                method,
                path,
                status_code,
                duration_ms,
                request_id,
            )

    def _content_length(self, scope) -> int | None:
        for raw_name, raw_value in scope.get("headers", []):
            if raw_name.lower() != b"content-length":
                continue
            try:
                value = int(raw_value)
            except (TypeError, ValueError):
                return None
            return max(0, value)
        return None
