from __future__ import annotations

import json
from collections import deque
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from hashlib import sha256
from math import ceil
from threading import Lock
from time import monotonic

from fastapi import Request

from app.core.exceptions import ApiError, AuthRateLimitError


MAX_AUTH_REQUEST_BYTES = 16_384


@dataclass(frozen=True)
class RateLimitBucket:
    key: str
    limit: int
    window_seconds: int


@dataclass(frozen=True)
class AuthRateLimitPolicy:
    operation: str
    ip_limit: int
    ip_window_seconds: int
    account_limit: int | None = None
    account_window_seconds: int | None = None


class InMemoryRateLimiter:
    """Small process-local sliding-window limiter.

    Keys contain an IP address or a one-way email digest, never a raw email. The
    lock makes checks atomic across threads. A distributed deployment must replace
    this with a shared store or an edge/WAF limiter.
    """

    def __init__(self, clock: Callable[[], float] = monotonic) -> None:
        self._clock = clock
        self._events: dict[str, deque[float]] = {}
        self._lock = Lock()
        self._checks = 0

    def enforce(self, buckets: Iterable[RateLimitBucket]) -> None:
        bucket_list = tuple(buckets)
        now = self._clock()
        retry_after = 0

        with self._lock:
            queues: list[tuple[RateLimitBucket, deque[float]]] = []
            for bucket in bucket_list:
                queue = self._events.setdefault(bucket.key, deque())
                cutoff = now - bucket.window_seconds
                while queue and queue[0] <= cutoff:
                    queue.popleft()
                queues.append((bucket, queue))
                if len(queue) >= bucket.limit:
                    retry_after = max(
                        retry_after,
                        ceil(bucket.window_seconds - (now - queue[0])),
                    )

            if retry_after:
                # Coarse value helps clients back off without exposing exact counters.
                retry_after = max(5, ((retry_after + 4) // 5) * 5)
                raise AuthRateLimitError(retry_after=retry_after)

            for _, queue in queues:
                queue.append(now)

            self._checks += 1
            if self._checks % 256 == 0:
                stale_before = now - 600
                stale_keys = [
                    key
                    for key, queue in self._events.items()
                    if not queue or queue[-1] <= stale_before
                ]
                for key in stale_keys:
                    self._events.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._events.clear()
            self._checks = 0


_AUTH_RATE_LIMITER = InMemoryRateLimiter()


async def _account_digest(request: Request) -> str | None:
    raw_body = await request.body()
    if len(raw_body) > MAX_AUTH_REQUEST_BYTES:
        # Never fall back to IP-only throttling for a valid, padded account
        # request: that would let an attacker bypass the per-email bucket.
        raise ApiError(413, "El cuerpo de autenticación excede el límite permitido.")
    try:
        body = json.loads(raw_body)
    except (UnicodeDecodeError, ValueError):
        return None
    if not isinstance(body, dict):
        return None
    email = body.get("email")
    if not isinstance(email, str):
        return None
    normalized_email = email.strip().casefold()
    if not normalized_email:
        return None
    return sha256(normalized_email.encode("utf-8")).hexdigest()


def auth_rate_limit(policy: AuthRateLimitPolicy):
    async def dependency(request: Request) -> None:
        client_host = request.client.host if request.client else "unknown"
        buckets = [
            RateLimitBucket(
                key=f"auth:{policy.operation}:ip:{client_host}",
                limit=policy.ip_limit,
                window_seconds=policy.ip_window_seconds,
            )
        ]
        if policy.account_limit and policy.account_window_seconds:
            digest = await _account_digest(request)
            if digest:
                buckets.append(
                    RateLimitBucket(
                        key=f"auth:{policy.operation}:account:{digest}",
                        limit=policy.account_limit,
                        window_seconds=policy.account_window_seconds,
                    )
                )
        _AUTH_RATE_LIMITER.enforce(buckets)

    return dependency


limit_register = auth_rate_limit(
    AuthRateLimitPolicy("register", 5, 60, account_limit=2, account_window_seconds=300)
)
limit_login = auth_rate_limit(
    AuthRateLimitPolicy("login", 20, 60, account_limit=8, account_window_seconds=300)
)
limit_send_otp = auth_rate_limit(
    AuthRateLimitPolicy("otp", 10, 60, account_limit=1, account_window_seconds=60)
)
limit_verify_otp = auth_rate_limit(
    AuthRateLimitPolicy("verify-otp", 30, 60, account_limit=10, account_window_seconds=300)
)
limit_forgot_password = auth_rate_limit(
    AuthRateLimitPolicy("forgot-password", 5, 60, account_limit=2, account_window_seconds=300)
)
limit_reset_password = auth_rate_limit(
    AuthRateLimitPolicy("reset-password", 10, 60)
)


def clear_auth_rate_limits() -> None:
    """Reset process-local counters; intended for deterministic tests."""
    _AUTH_RATE_LIMITER.clear()
