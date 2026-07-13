from __future__ import annotations

import asyncio
from types import SimpleNamespace
from uuid import UUID

import pytest

from app.core.exceptions import ApiError
from app.domain.schemas.resources.user_statistics import LearningEventCreate
from app.infra.repositories.user_statistics import UserStatisticsRepository


USER_ID = UUID("00000000-0000-0000-0000-000000000001")
NOTEBOOK_ID = UUID("00000000-0000-0000-0000-000000000010")


class FakeRpcQuery:
    def __init__(self, *, data=None, error: Exception | None = None) -> None:
        self.data = data
        self.error = error

    def execute(self):
        if self.error:
            raise self.error
        return SimpleNamespace(data=self.data)


class FakeClient:
    def __init__(self, *, data=None, error: Exception | None = None) -> None:
        self.data = data
        self.error = error
        self.function_name: str | None = None
        self.params: dict | None = None

    def rpc(self, function_name, params):
        self.function_name = function_name
        self.params = params
        return FakeRpcQuery(data=self.data, error=self.error)


def _event() -> LearningEventCreate:
    return LearningEventCreate(
        notebook_id=NOTEBOOK_ID,
        activity_type="flashcard_reviewed",
        quantity=5,
        duration_seconds=120,
    )


def test_repository_uses_actor_derived_atomic_rpc() -> None:
    client = FakeClient(
        data=[
            {
                "event_id": "00000000-0000-0000-0000-000000000060",
                "user_id": str(USER_ID),
                "notebook_id": str(NOTEBOOK_ID),
                "activity_type": "flashcard_reviewed",
                "quantity": 5,
                "duration_seconds": 120,
                "occurred_at": "2026-07-13T12:00:00Z",
                "idempotency_key": "not-returned-to-client",
                "metadata": {},
            }
        ]
    )
    repository = UserStatisticsRepository(client=client)

    result = asyncio.run(
        repository.record_event(USER_ID, _event(), "flashcards:batch-0001")
    )

    assert client.function_name == "record_user_learning_event"
    assert client.params is not None
    assert "p_user_id" not in client.params
    assert client.params["p_idempotency_key"] == "flashcards:batch-0001"
    assert result["user_id"] == str(USER_ID)
    assert "idempotency_key" not in result
    assert "metadata" not in result


@pytest.mark.parametrize(
    ("provider_message", "status_code"),
    [
        ("learning_event_rate_limit", 429),
        ("learning_event_daily_limit", 429),
        ("idempotency_key_reused", 409),
    ],
)
def test_repository_maps_rpc_failures_without_leaking_provider_errors(
    provider_message: str, status_code: int
) -> None:
    client = FakeClient(error=RuntimeError(provider_message))
    repository = UserStatisticsRepository(client=client)

    with pytest.raises(ApiError) as captured:
        asyncio.run(
            repository.record_event(USER_ID, _event(), "flashcards:batch-0001")
        )

    assert captured.value.status_code == status_code
    assert provider_message not in captured.value.message
