from typing import Protocol

from app.domain.schemas.resources.exams import (
    ExamQuestionRepositoryCreateRequest,
    ExamQuestionRepositoryDeleteRequest,
    ExamRepositoryCreateRequest,
    ExamRepositoryDeleteRequest,
    ExamRepositoryGetRequest,
    ExamRepositoryListRequest,
    ExamRepositoryUpdateRequest,
)


class ExamRepository(Protocol):
    async def list(self, request: ExamRepositoryListRequest) -> list[dict]:
        raise NotImplementedError

    async def get(self, request: ExamRepositoryGetRequest) -> dict | None:
        raise NotImplementedError

    async def create(self, request: ExamRepositoryCreateRequest) -> dict:
        raise NotImplementedError

    async def update(self, request: ExamRepositoryUpdateRequest) -> dict | None:
        raise NotImplementedError

    async def delete(self, request: ExamRepositoryDeleteRequest) -> dict | None:
        raise NotImplementedError


class ExamQuestionRepository(Protocol):
    async def create(self, request: ExamQuestionRepositoryCreateRequest) -> dict:
        raise NotImplementedError

    async def delete(self, request: ExamQuestionRepositoryDeleteRequest) -> dict | None:
        raise NotImplementedError
