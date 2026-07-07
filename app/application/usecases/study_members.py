from datetime import UTC, datetime

from app.core.exceptions import EmptyPayloadError, ResourceNotFoundError
from app.domain.interfaces import StudyMemberRepository
from app.domain.schemas.crud import CrudItemResponse, CrudListResponse
from app.domain.schemas.resources.study_members import (
    StudyMemberCreateRequest,
    StudyMemberDeleteRequest,
    StudyMemberListRequest,
    StudyMemberPath,
    StudyMemberRepositoryCreateRequest,
    StudyMemberRepositoryDeleteRequest,
    StudyMemberRepositoryGetRequest,
    StudyMemberRepositoryListRequest,
    StudyMemberRepositoryUpdateRequest,
    StudyMemberUpdateRequest,
)


class StudyMemberUseCase:
    def __init__(self, repository: StudyMemberRepository) -> None:
        self.repository = repository

    async def list(self, request: StudyMemberListRequest) -> CrudListResponse:
        data = await self.repository.list(
            StudyMemberRepositoryListRequest(limit=request.limit, offset=request.offset)
        )
        return CrudListResponse(data=data, limit=request.limit, offset=request.offset)

    async def get(self, request: StudyMemberPath) -> CrudItemResponse:
        data = await self.repository.get(
            StudyMemberRepositoryGetRequest(member_id=request.member_id)
        )
        if data is None:
            raise ResourceNotFoundError()
        return CrudItemResponse(data=data)

    async def create(self, request: StudyMemberCreateRequest) -> CrudItemResponse:
        data = await self.repository.create(
            StudyMemberRepositoryCreateRequest(payload=request.payload)
        )
        return CrudItemResponse(data=data)

    async def update(self, request: StudyMemberUpdateRequest) -> CrudItemResponse:
        if not request.payload.model_dump(exclude_unset=True):
            raise EmptyPayloadError()
        data = await self.repository.update(
            StudyMemberRepositoryUpdateRequest(
                member_id=request.member_id,
                payload=request.payload,
                updated_at=datetime.now(UTC),
            )
        )
        if data is None:
            raise ResourceNotFoundError()
        return CrudItemResponse(data=data)

    async def delete(self, request: StudyMemberDeleteRequest) -> CrudItemResponse:
        data = await self.repository.delete(
            StudyMemberRepositoryDeleteRequest(member_id=request.member_id)
        )
        if data is None:
            raise ResourceNotFoundError()
        return CrudItemResponse(data=data)
