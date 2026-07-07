from datetime import UTC, datetime

from app.core.exceptions import EmptyPayloadError, ResourceNotFoundError
from app.domain.interfaces import DocumentRepository
from app.domain.schemas.crud import CrudItemResponse, CrudListResponse
from app.domain.schemas.resources.documents import (
    DocumentCreateRequest,
    DocumentDeleteRequest,
    DocumentListRequest,
    DocumentPath,
    DocumentRepositoryCreateRequest,
    DocumentRepositoryDeleteRequest,
    DocumentRepositoryGetRequest,
    DocumentRepositoryListRequest,
    DocumentRepositoryUpdateRequest,
    DocumentUpdateRequest,
)


class DocumentUseCase:
    def __init__(self, repository: DocumentRepository) -> None:
        self.repository = repository

    async def list(self, request: DocumentListRequest) -> CrudListResponse:
        data = await self.repository.list(
            DocumentRepositoryListRequest(limit=request.limit, offset=request.offset)
        )
        return CrudListResponse(data=data, limit=request.limit, offset=request.offset)

    async def get(self, request: DocumentPath) -> CrudItemResponse:
        data = await self.repository.get(
            DocumentRepositoryGetRequest(document_id=request.document_id)
        )
        if data is None:
            raise ResourceNotFoundError()
        return CrudItemResponse(data=data)

    async def create(self, request: DocumentCreateRequest) -> CrudItemResponse:
        data = await self.repository.create(DocumentRepositoryCreateRequest(payload=request.payload))
        return CrudItemResponse(data=data)

    async def update(self, request: DocumentUpdateRequest) -> CrudItemResponse:
        if not request.payload.model_dump(exclude_unset=True):
            raise EmptyPayloadError()
        data = await self.repository.update(
            DocumentRepositoryUpdateRequest(
                document_id=request.document_id,
                payload=request.payload,
                updated_at=datetime.now(UTC),
            )
        )
        if data is None:
            raise ResourceNotFoundError()
        return CrudItemResponse(data=data)

    async def delete(self, request: DocumentDeleteRequest) -> CrudItemResponse:
        data = await self.repository.delete(
            DocumentRepositoryDeleteRequest(document_id=request.document_id)
        )
        if data is None:
            raise ResourceNotFoundError()
        return CrudItemResponse(data=data)
