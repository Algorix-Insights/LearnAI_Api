from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import pytest

from app.application.usecases.user_statistics import UserStatisticsUseCase
from app.core.exceptions import ForbiddenError
from app.domain.schemas.resources.user_statistics import (
    LearningEventCreate,
    UserStatisticsRequest,
)


USER_ID = UUID("00000000-0000-0000-0000-000000000001")
NOTEBOOK_ID = UUID("00000000-0000-0000-0000-000000000010")
SECOND_NOTEBOOK_ID = UUID("00000000-0000-0000-0000-000000000011")
EXAM_ID = UUID("00000000-0000-0000-0000-000000000020")


class FakeStatisticsRepository:
    def __init__(self) -> None:
        now = datetime.now(UTC)
        self.snapshot: dict[str, list[dict[str, Any]]] = {
            "notebooks": [
                {
                    "notebook_id": str(NOTEBOOK_ID),
                    "name": "Algoritmos",
                    "due_date": (now + timedelta(days=2)).isoformat(),
                    "status": "active",
                    "is_dominated": False,
                },
                {
                    "notebook_id": str(SECOND_NOTEBOOK_ID),
                    "name": "Bases de datos",
                    "due_date": None,
                    "status": "active",
                    "is_dominated": True,
                },
            ],
            "exams": [
                {
                    "exam_id": str(EXAM_ID),
                    "notebook_id": str(NOTEBOOK_ID),
                    "name": "Parcial 1",
                    "status": "active",
                }
            ],
            "attempts": [
                {
                    "attempt_id": "00000000-0000-0000-0000-000000000030",
                    "exam_id": str(EXAM_ID),
                    "score": 65,
                    "status": "completed",
                    "completed_at": now.isoformat(),
                    "spent_time": 600,
                }
            ],
            "flashcards": [
                {
                    "flashcard_id": "00000000-0000-0000-0000-000000000040",
                    "notebook_id": str(NOTEBOOK_ID),
                    "spent_time": 0,
                }
            ],
            "events": [
                {
                    "event_id": "00000000-0000-0000-0000-000000000050",
                    "user_id": str(USER_ID),
                    "notebook_id": str(NOTEBOOK_ID),
                    "activity_type": "flashcard_reviewed",
                    "quantity": 3,
                    "duration_seconds": 300,
                    "occurred_at": now.isoformat(),
                }
            ],
        }
        self.recorded: dict[str, Any] | None = None

    async def load_snapshot(self, user_id: UUID) -> dict[str, list[dict[str, Any]]]:
        assert user_id == USER_ID
        return self.snapshot

    async def record_event(
        self, user_id: UUID, event: LearningEventCreate
    ) -> dict[str, Any]:
        self.recorded = {"user_id": str(user_id), **event.model_dump(mode="json")}
        return {
            "event_id": "00000000-0000-0000-0000-000000000060",
            "occurred_at": datetime.now(UTC).isoformat(),
            **self.recorded,
        }


def test_statistics_builds_dashboard_from_user_scoped_data() -> None:
    repository = FakeStatisticsRepository()
    use_case = UserStatisticsUseCase(repository)

    response = asyncio.run(
        use_case.get(
            USER_ID,
            UserStatisticsRequest(period="week", timezone="America/Cancun"),
        )
    )

    assert response.data.overview.average_score == 65
    assert response.data.overview.completed_exams == 1
    assert response.data.overview.notebooks_dominated == 1
    assert response.data.overview.total_study_seconds == 900
    assert response.data.reinforcement[0].name == "Algoritmos"
    assert response.data.reinforcement[0].flashcards_count == 1
    assert response.data.upcoming[0].notebook_id == NOTEBOOK_ID
    assert response.data.streak.current_days == 1
    assert response.data.time_by_notebook[0].study_seconds == 900
    assert response.data.recent_activity[0].activity_type in {
        "exam_completed",
        "flashcard_reviewed",
    }


def test_record_learning_event_uses_authenticated_user_and_checks_access() -> None:
    repository = FakeStatisticsRepository()
    use_case = UserStatisticsUseCase(repository)
    event = LearningEventCreate(
        notebook_id=NOTEBOOK_ID,
        activity_type="study_session",
        duration_seconds=1200,
    )

    response = asyncio.run(use_case.record(USER_ID, event))

    assert response.data.user_id == USER_ID
    assert repository.recorded is not None
    assert repository.recorded["user_id"] == str(USER_ID)

    forbidden_event = event.model_copy(
        update={"notebook_id": UUID("00000000-0000-0000-0000-000000000099")}
    )
    with pytest.raises(ForbiddenError):
        asyncio.run(use_case.record(USER_ID, forbidden_event))
