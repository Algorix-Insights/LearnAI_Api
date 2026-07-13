from typing import Any, Protocol
from uuid import UUID

from app.domain.schemas.resources.user_statistics import LearningEventCreate


class UserStatisticsRepository(Protocol):
    async def load_snapshot(self, user_id: UUID) -> dict[str, list[dict[str, Any]]]:
        raise NotImplementedError

    async def record_event(
        self,
        user_id: UUID,
        event: LearningEventCreate,
        idempotency_key: str,
    ) -> dict[str, Any]:
        raise NotImplementedError
