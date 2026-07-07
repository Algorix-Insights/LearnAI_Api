from datetime import UTC, datetime

from app.core.exceptions import ResourceNotFoundError
from app.domain.interfaces import NotebookRepository
from app.domain.services import NotebookService
from app.domain.schemas.resources.notebooks import (
    NotebookCreateRequest,
    NotebookDeleteRequest,
    NotebookListResponse,
    NotebookListRequest,
    NotebookPath,
    NotebookRepositoryCreateRequest,
    NotebookRepositoryDeleteRequest,
    NotebookRepositoryGetRequest,
    NotebookRepositoryListRequest,
    NotebookRepositoryUpdateRequest,
    NotebookResponse,
    NotebookUpdateRequest,
)


class NotebookUseCase:
    def __init__(
        self, repository: NotebookRepository, service: NotebookService | None = None
    ) -> None:
        self.repository = repository
        self.service = service or NotebookService()

    async def list(self, request: NotebookListRequest) -> NotebookListResponse:
        data = await self.repository.list(
            NotebookRepositoryListRequest(limit=request.limit, offset=request.offset)
        )
        return NotebookListResponse(data=data, limit=request.limit, offset=request.offset)

    async def get(self, request: NotebookPath) -> NotebookResponse:
        data = await self.repository.get(
            NotebookRepositoryGetRequest(notebook_id=request.notebook_id)
        )
        if data is None:
            raise ResourceNotFoundError()
        return NotebookResponse(data=data)

    async def create(self, request: NotebookCreateRequest) -> NotebookResponse:
        request = self.service.prepare_create(request)
        data = await self.repository.create(NotebookRepositoryCreateRequest(payload=request.payload))
        return NotebookResponse(data=data)

    async def update(self, request: NotebookUpdateRequest) -> NotebookResponse:
        request = self.service.prepare_update(request)
        data = await self.repository.update(
            NotebookRepositoryUpdateRequest(
                notebook_id=request.notebook_id,
                payload=request.payload,
                updated_at=datetime.now(UTC),
            )
        )
        if data is None:
            raise ResourceNotFoundError()
        return NotebookResponse(data=data)

    async def delete(self, request: NotebookDeleteRequest) -> NotebookResponse:
        data = await self.repository.delete(
            NotebookRepositoryDeleteRequest(notebook_id=request.notebook_id)
        )
        if data is None:
            raise ResourceNotFoundError()
        return NotebookResponse(data=data)
