from typing import Protocol

from app.domain.schemas.resources.question_options import (
    QuestionOptionRepositoryCreateRequest,
    QuestionOptionRepositoryDeleteRequest,
    QuestionOptionRepositoryGetRequest,
    QuestionOptionRepositoryListRequest,
    QuestionOptionRepositoryUpdateRequest,
)


class QuestionOptionRepository(Protocol):
    async def list(self, request: QuestionOptionRepositoryListRequest) -> list[dict]:
        raise NotImplementedError

    async def get(self, request: QuestionOptionRepositoryGetRequest) -> dict | None:
        raise NotImplementedError

    async def create(self, request: QuestionOptionRepositoryCreateRequest) -> dict:
        raise NotImplementedError

    async def update(self, request: QuestionOptionRepositoryUpdateRequest) -> dict | None:
        raise NotImplementedError

    async def delete(self, request: QuestionOptionRepositoryDeleteRequest) -> dict | None:
        raise NotImplementedError
