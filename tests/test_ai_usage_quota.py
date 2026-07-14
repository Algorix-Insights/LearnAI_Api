from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from app.api.dependencies import _ai_usage_repository
from app.core.config import Settings
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


def test_ai_usage_quota_is_disabled_by_default(monkeypatch) -> None:
    monkeypatch.delenv("AI_USAGE_QUOTA_ENABLED", raising=False)
    settings = Settings(_env_file=None)

    assert settings.ai_usage_quota_enabled is False
    assert _ai_usage_repository(FakeClient(), settings) is None


def test_ai_usage_quota_can_be_reenabled_explicitly() -> None:
    repository = _ai_usage_repository(
        FakeClient(),
        Settings(ai_usage_quota_enabled=True, _env_file=None),
    )

    assert isinstance(repository, AiUsageRepository)


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
