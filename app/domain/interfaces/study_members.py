from typing import Protocol

from app.domain.schemas.resources.study_members import (
    StudyMemberRepositoryCreateRequest,
    StudyMemberRepositoryDeleteRequest,
    StudyMemberRepositoryGetRequest,
    StudyMemberRepositoryListRequest,
    StudyMemberRepositoryUpdateRequest,
)


class StudyMemberRepository(Protocol):
    async def list(self, request: StudyMemberRepositoryListRequest) -> list[dict]:
        raise NotImplementedError

    async def get(self, request: StudyMemberRepositoryGetRequest) -> dict | None:
        raise NotImplementedError

    async def create(self, request: StudyMemberRepositoryCreateRequest) -> dict:
        raise NotImplementedError

    async def update(self, request: StudyMemberRepositoryUpdateRequest) -> dict | None:
        raise NotImplementedError

    async def delete(self, request: StudyMemberRepositoryDeleteRequest) -> dict | None:
        raise NotImplementedError
