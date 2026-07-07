from typing import Protocol

from app.domain.schemas.resources.user_answers import (
    UserAnswerRepositoryCreateRequest,
    UserAnswerRepositoryDeleteRequest,
    UserAnswerRepositoryGetRequest,
    UserAnswerRepositoryListRequest,
    UserAnswerRepositoryUpdateRequest,
)


class UserAnswerRepository(Protocol):
    async def list(self, request: UserAnswerRepositoryListRequest) -> list[dict]:
        raise NotImplementedError

    async def get(self, request: UserAnswerRepositoryGetRequest) -> dict | None:
        raise NotImplementedError

    async def create(self, request: UserAnswerRepositoryCreateRequest) -> dict:
        raise NotImplementedError

    async def update(self, request: UserAnswerRepositoryUpdateRequest) -> dict | None:
        raise NotImplementedError

    async def delete(self, request: UserAnswerRepositoryDeleteRequest) -> dict | None:
        raise NotImplementedError
