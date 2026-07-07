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

    async def list(self, request: TagListRequest) -> TagListResponse:
        data = await self.repository.list(
            TagRepositoryListRequest(limit=request.limit, offset=request.offset)
        )
        return TagListResponse(data=data, limit=request.limit, offset=request.offset)

    async def get(self, request: TagPath) -> TagResponse:
        data = await self.repository.get(TagRepositoryGetRequest(tag_id=request.tag_id))
        if data is None:
            raise ResourceNotFoundError()
        return TagResponse(data=data)

    async def create(self, request: TagCreateRequest) -> TagResponse:
        data = await self.repository.create(TagRepositoryCreateRequest(payload=request.payload))
        return TagResponse(data=data)

    async def update(self, request: TagUpdateRequest) -> TagResponse:
        if not request.payload.model_dump(exclude_unset=True):
            raise EmptyPayloadError()
        data = await self.repository.update(
            TagRepositoryUpdateRequest(tag_id=request.tag_id, payload=request.payload)
        )
        if data is None:
            raise ResourceNotFoundError()
        return TagResponse(data=data)

    async def delete(self, request: TagDeleteRequest) -> TagResponse:
        data = await self.repository.delete(TagRepositoryDeleteRequest(tag_id=request.tag_id))
        if data is None:
            raise ResourceNotFoundError()
        return TagResponse(data=data)
