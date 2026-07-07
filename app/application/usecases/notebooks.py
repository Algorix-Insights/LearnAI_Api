from datetime import UTC, datetime

from app.core.exceptions import ResourceNotFoundError
from app.domain.interfaces import NotebookRepository
from app.domain.services import NotebookService
from app.domain.schemas.crud import CrudItemResponse, CrudListResponse
from app.domain.schemas.resources.notebooks import (
    NotebookCreateRequest,
    NotebookDeleteRequest,
    NotebookListRequest,
    NotebookPath,
    NotebookRepositoryCreateRequest,
    NotebookRepositoryDeleteRequest,
    NotebookRepositoryGetRequest,
    NotebookRepositoryListRequest,
    NotebookRepositoryUpdateRequest,
    NotebookUpdateRequest,
)


class NotebookUseCase:
    def __init__(
        self, repository: NotebookRepository, service: NotebookService | None = None
    ) -> None:
        self.repository = repository
        self.service = service or NotebookService()

    async def list(self, request: NotebookListRequest) -> CrudListResponse:
        data = await self.repository.list(
            NotebookRepositoryListRequest(limit=request.limit, offset=request.offset)
        )
        return CrudListResponse(data=data, limit=request.limit, offset=request.offset)

    async def get(self, request: NotebookPath) -> CrudItemResponse:
        data = await self.repository.get(
            NotebookRepositoryGetRequest(notebook_id=request.notebook_id)
        )
        if data is None:
            raise ResourceNotFoundError()
        return CrudItemResponse(data=data)

    async def create(self, request: NotebookCreateRequest) -> CrudItemResponse:
        request = self.service.prepare_create(request)
        data = await self.repository.create(NotebookRepositoryCreateRequest(payload=request.payload))
        return CrudItemResponse(data=data)

    async def update(self, request: NotebookUpdateRequest) -> CrudItemResponse:
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
        return CrudItemResponse(data=data)

    async def delete(self, request: NotebookDeleteRequest) -> CrudItemResponse:
        data = await self.repository.delete(
            NotebookRepositoryDeleteRequest(notebook_id=request.notebook_id)
        )
        if data is None:
            raise ResourceNotFoundError()
        return CrudItemResponse(data=data)
