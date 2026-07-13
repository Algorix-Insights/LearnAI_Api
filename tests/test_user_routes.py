from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_current_user,
    get_user_profile_use_case,
    get_user_statistics_use_case,
)
from app.domain.schemas.resources.user_profile import ProfilePhotoResponse
from app.domain.schemas.resources.user_statistics import (
    LearningEventResponse,
    StatisticsOverview,
    StreakStatistics,
    UserStatisticsData,
    UserStatisticsResponse,
)
from app.domain.schemas.resources.users import UserRead
from app.main import app


USER_ID = UUID("00000000-0000-0000-0000-000000000001")


class FakeProfileUseCase:
    def __init__(self) -> None:
        self.actor: UUID | None = None

    async def upload_photo(self, *, user_id, file):
        self.actor = user_id
        return ProfilePhotoResponse(
            data={
                "user_id": user_id,
                "storage_path": f"{user_id}/profile.png",
                "mime_type": "image/png",
                "size_bytes": 8,
                "url": "https://signed.example/avatar",
                "expires_in": 3600,
            }
        )


class FakeStatisticsUseCase:
    def __init__(self) -> None:
        self.actor: UUID | None = None
        self.idempotency_key: str | None = None

    async def get(self, user_id, request):
        self.actor = user_id
        return UserStatisticsResponse(
            data=UserStatisticsData(
                overview=StatisticsOverview(total_notebooks=2),
                streak=StreakStatistics(),
                generated_at=datetime.now(UTC),
            )
        )

    async def record(self, user_id, payload, idempotency_key):
        self.actor = user_id
        self.idempotency_key = idempotency_key
        return LearningEventResponse(
            data={
                "event_id": "00000000-0000-0000-0000-000000000060",
                "user_id": user_id,
                "notebook_id": payload.notebook_id,
                "activity_type": payload.activity_type,
                "quantity": payload.quantity,
                "duration_seconds": payload.duration_seconds,
                "occurred_at": datetime.now(UTC),
            }
        )


def test_profile_photo_route_lives_under_users_me_and_uses_jwt_actor() -> None:
    profile = FakeProfileUseCase()
    app.dependency_overrides[get_current_user] = lambda: UserRead(user_id=USER_ID)
    app.dependency_overrides[get_user_profile_use_case] = lambda: profile
    client = TestClient(app, headers={"Authorization": "Bearer test-token"})

    response = client.post(
        "/api/v1/users/me/profile-photo",
        files={"file": ("avatar.png", b"\x89PNG\r\n\x1a\n", "image/png")},
    )

    assert response.status_code == 201
    assert response.json()["data"]["user_id"] == str(USER_ID)
    assert profile.actor == USER_ID
    app.dependency_overrides.clear()


def test_user_statistics_route_uses_jwt_actor() -> None:
    statistics = FakeStatisticsUseCase()
    app.dependency_overrides[get_current_user] = lambda: UserRead(user_id=USER_ID)
    app.dependency_overrides[get_user_statistics_use_case] = lambda: statistics
    client = TestClient(app, headers={"Authorization": "Bearer test-token"})

    response = client.get(
        "/api/v1/users/me/statistics?period=week&timezone=America%2FCancun"
    )

    assert response.status_code == 200
    assert response.json()["data"]["overview"]["total_notebooks"] == 2
    assert statistics.actor == USER_ID
    app.dependency_overrides.clear()


def test_learning_event_requires_and_forwards_idempotency_key() -> None:
    statistics = FakeStatisticsUseCase()
    app.dependency_overrides[get_current_user] = lambda: UserRead(user_id=USER_ID)
    app.dependency_overrides[get_user_statistics_use_case] = lambda: statistics
    client = TestClient(app, headers={"Authorization": "Bearer test-token"})
    payload = {
        "notebook_id": "00000000-0000-0000-0000-000000000010",
        "activity_type": "study_session",
        "quantity": 1,
        "duration_seconds": 600,
    }

    missing = client.post("/api/v1/users/me/learning-events", json=payload)
    response = client.post(
        "/api/v1/users/me/learning-events",
        json=payload,
        headers={"Idempotency-Key": "study-session:0001"},
    )

    assert missing.status_code == 422
    assert response.status_code == 201
    assert statistics.actor == USER_ID
    assert statistics.idempotency_key == "study-session:0001"
    app.dependency_overrides.clear()
