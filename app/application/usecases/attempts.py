from app.core.exceptions import ResourceNotFoundError
from app.domain.interfaces import AttemptRepository
from app.domain.services import AttemptService
from app.domain.schemas.resources.attempts import (
    AttemptCreateRequest,
    AttemptDeleteRequest,
    AttemptListResponse,
    AttemptListRequest,
    AttemptPath,
    AttemptRepositoryCreateRequest,
    AttemptRepositoryDeleteRequest,
    AttemptRepositoryGetRequest,
    AttemptRepositoryListRequest,
    AttemptRepositoryUpdateRequest,
    AttemptResponse,
    AttemptUpdateRequest,
)


class AttemptUseCase:
    def __init__(
        self, repository: AttemptRepository, service: AttemptService | None = None
    ) -> None:
        self.repository = repository
        self.service = service or AttemptService()

    async def list(self, request: AttemptListRequest) -> AttemptListResponse:
        data = await self.repository.list(
            AttemptRepositoryListRequest(limit=request.limit, offset=request.offset)
        )
        return AttemptListResponse(data=data, limit=request.limit, offset=request.offset)

    async def get(self, request: AttemptPath) -> AttemptResponse:
        data = await self.repository.get(AttemptRepositoryGetRequest(attempt_id=request.attempt_id))
        if data is None:
            raise ResourceNotFoundError()
        return AttemptResponse(data=data)

    async def create(self, request: AttemptCreateRequest) -> AttemptResponse:
        request = self.service.prepare_create(request)
        data = await self.repository.create(AttemptRepositoryCreateRequest(payload=request.payload))
        return AttemptResponse(data=data)

    async def update(self, request: AttemptUpdateRequest) -> AttemptResponse:
        request = self.service.prepare_update(request)
        data = await self.repository.update(
            AttemptRepositoryUpdateRequest(attempt_id=request.attempt_id, payload=request.payload)
        )
        if data is None:
            raise ResourceNotFoundError()
        return AttemptResponse(data=data)

    async def delete(self, request: AttemptDeleteRequest) -> AttemptResponse:
        data = await self.repository.delete(
            AttemptRepositoryDeleteRequest(attempt_id=request.attempt_id)
        )
        if data is None:
            raise ResourceNotFoundError()
        return AttemptResponse(data=data)
