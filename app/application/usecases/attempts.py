from app.core.exceptions import EmptyPayloadError, ResourceNotFoundError
from app.domain.interfaces import AttemptRepository
from app.domain.schemas.crud import CrudItemResponse, CrudListResponse
from app.domain.schemas.resources.attempts import (
    AttemptCreateRequest,
    AttemptDeleteRequest,
    AttemptListRequest,
    AttemptPath,
    AttemptRepositoryCreateRequest,
    AttemptRepositoryDeleteRequest,
    AttemptRepositoryGetRequest,
    AttemptRepositoryListRequest,
    AttemptRepositoryUpdateRequest,
    AttemptUpdateRequest,
)


class AttemptUseCase:
    def __init__(self, repository: AttemptRepository) -> None:
        self.repository = repository

    async def list(self, request: AttemptListRequest) -> CrudListResponse:
        data = await self.repository.list(
            AttemptRepositoryListRequest(limit=request.limit, offset=request.offset)
        )
        return CrudListResponse(data=data, limit=request.limit, offset=request.offset)

    async def get(self, request: AttemptPath) -> CrudItemResponse:
        data = await self.repository.get(AttemptRepositoryGetRequest(attempt_id=request.attempt_id))
        if data is None:
            raise ResourceNotFoundError()
        return CrudItemResponse(data=data)

    async def create(self, request: AttemptCreateRequest) -> CrudItemResponse:
        data = await self.repository.create(AttemptRepositoryCreateRequest(payload=request.payload))
        return CrudItemResponse(data=data)

    async def update(self, request: AttemptUpdateRequest) -> CrudItemResponse:
        if not request.payload.model_dump(exclude_unset=True):
            raise EmptyPayloadError()
        data = await self.repository.update(
            AttemptRepositoryUpdateRequest(attempt_id=request.attempt_id, payload=request.payload)
        )
        if data is None:
            raise ResourceNotFoundError()
        return CrudItemResponse(data=data)

    async def delete(self, request: AttemptDeleteRequest) -> CrudItemResponse:
        data = await self.repository.delete(
            AttemptRepositoryDeleteRequest(attempt_id=request.attempt_id)
        )
        if data is None:
            raise ResourceNotFoundError()
        return CrudItemResponse(data=data)
