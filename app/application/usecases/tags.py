from uuid import UUID

from app.core.exceptions import EmptyPayloadError, ResourceNotFoundError
from app.domain.interfaces import TagRepository
from app.domain.schemas.resources.tags import (
    TagCreateRequest,
    TagDeleteRequest,
    TagListResponse,
    TagListRequest,
    TagPath,
    TagRepositoryCreateRequest,
    TagRepositoryDeleteRequest,
    TagRepositoryGetRequest,
    TagRepositoryListRequest,
    TagRepositoryUpdateRequest,
    TagResponse,
    TagUpdateRequest,
)


class TagUseCase:
    def __init__(self, repository: TagRepository) -> None:
        self.repository = repository

    async def list(self, request: TagListRequest, *, user_id: UUID) -> TagListResponse:
        data = await self.repository.list(
            TagRepositoryListRequest(
                limit=request.limit,
                offset=request.offset,
                user_id=user_id,
            )
        )
        return TagListResponse(data=data, limit=request.limit, offset=request.offset)

    async def get(self, request: TagPath, *, user_id: UUID) -> TagResponse:
        data = await self.repository.get(
            TagRepositoryGetRequest(tag_id=request.tag_id, user_id=user_id)
        )
        if data is None:
            raise ResourceNotFoundError()
        return TagResponse(data=data)

    async def create(self, request: TagCreateRequest, *, user_id: UUID) -> TagResponse:
        data = await self.repository.create(
            TagRepositoryCreateRequest(payload=request.payload, user_id=user_id)
        )
        return TagResponse(data=data)

    async def update(self, request: TagUpdateRequest, *, user_id: UUID) -> TagResponse:
        if not request.payload.model_dump(exclude_unset=True):
            raise EmptyPayloadError()
        data = await self.repository.update(
            TagRepositoryUpdateRequest(
                tag_id=request.tag_id,
                payload=request.payload,
                user_id=user_id,
            )
        )
        if data is None:
            raise ResourceNotFoundError()
        return TagResponse(data=data)

    async def delete(self, request: TagDeleteRequest, *, user_id: UUID) -> TagResponse:
        data = await self.repository.delete(
            TagRepositoryDeleteRequest(tag_id=request.tag_id, user_id=user_id)
        )
        if data is None:
            raise ResourceNotFoundError()
        return TagResponse(data=data)
