from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from app.core.exceptions import ApiError
from app.infra.repositories.ai_usage import AiUsageRepository


class FakeQuery:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error

    def execute(self):
        if self.error:
            raise self.error
        return SimpleNamespace(data=None)


class FakeClient:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.calls: list[tuple[str, dict]] = []

    def rpc(self, name: str, params: dict) -> FakeQuery:
        self.calls.append((name, params))
        return FakeQuery(self.error)


def test_ai_usage_reservation_passes_actor_to_service_only_rpc() -> None:
    client = FakeClient()
    repository = AiUsageRepository(client)

    asyncio.run(repository.reserve(actor_id="actor-id", operation="exam"))

    assert client.calls == [
        (
            "reserve_ai_usage",
            {"p_actor_id": "actor-id", "p_operation": "exam", "p_units": 1},
        )
    ]


def test_ai_usage_can_reserve_multiple_grading_units_atomically() -> None:
    client = FakeClient()
    repository = AiUsageRepository(client)

    asyncio.run(
        repository.reserve(
            actor_id="actor-id",
            operation="exam_grading",
            units=4,
        )
    )

    assert client.calls[0][1]["p_units"] == 4


def test_ai_usage_quota_maps_to_safe_429() -> None:
    client = FakeClient(RuntimeError("ai_usage_rate_limit internal database detail"))
    repository = AiUsageRepository(client)

    with pytest.raises(ApiError) as captured:
        asyncio.run(repository.reserve(actor_id="actor-id", operation="chat"))

    assert captured.value.status_code == 429
    assert captured.value.headers == {"Retry-After": "0"}
    assert "database detail" not in captured.value.message
