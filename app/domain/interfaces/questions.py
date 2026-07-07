from typing import Protocol

from app.domain.schemas.resources.questions import (
    QuestionRepositoryCreateRequest,
    QuestionRepositoryDeleteRequest,
    QuestionRepositoryGetRequest,
    QuestionRepositoryListRequest,
    QuestionRepositoryUpdateRequest,
)


class QuestionRepository(Protocol):
    async def list(self, request: QuestionRepositoryListRequest) -> list[dict]:
        raise NotImplementedError

    async def get(self, request: QuestionRepositoryGetRequest) -> dict | None:
        raise NotImplementedError

    async def create(self, request: QuestionRepositoryCreateRequest) -> dict:
        raise NotImplementedError

    async def update(self, request: QuestionRepositoryUpdateRequest) -> dict | None:
        raise NotImplementedError

    async def delete(self, request: QuestionRepositoryDeleteRequest) -> dict | None:
        raise NotImplementedError
