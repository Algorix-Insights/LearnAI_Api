from app.core.exceptions import EmptyPayloadError, ResourceNotFoundError
from app.domain.interfaces import DocumentChunkRepository
from app.domain.schemas.resources.document_chunks import (
    DocumentChunkCreateRequest,
    DocumentChunkDeleteRequest,
    DocumentChunkListResponse,
    DocumentChunkListRequest,
    DocumentChunkPath,
    DocumentChunkRepositoryCreateRequest,
    DocumentChunkRepositoryDeleteRequest,
    DocumentChunkRepositoryGetRequest,
    DocumentChunkRepositoryListRequest,
    DocumentChunkRepositoryUpdateRequest,
    DocumentChunkResponse,
    DocumentChunkUpdateRequest,
)


class DocumentChunkUseCase:
    def __init__(self, repository: DocumentChunkRepository) -> None:
        self.repository = repository

    async def list(self, request: DocumentChunkListRequest) -> DocumentChunkListResponse:
        data = await self.repository.list(
            DocumentChunkRepositoryListRequest(limit=request.limit, offset=request.offset)
        )
        return DocumentChunkListResponse(data=data, limit=request.limit, offset=request.offset)

    async def get(self, request: DocumentChunkPath) -> DocumentChunkResponse:
        data = await self.repository.get(
            DocumentChunkRepositoryGetRequest(chunk_id=request.chunk_id)
        )
        if data is None:
            raise ResourceNotFoundError()
        return DocumentChunkResponse(data=data)

    async def create(self, request: DocumentChunkCreateRequest) -> DocumentChunkResponse:
        data = await self.repository.create(
            DocumentChunkRepositoryCreateRequest(payload=request.payload)
        )
        return DocumentChunkResponse(data=data)

    async def update(self, request: DocumentChunkUpdateRequest) -> DocumentChunkResponse:
        if not request.payload.model_dump(exclude_unset=True):
            raise EmptyPayloadError()
        data = await self.repository.update(
            DocumentChunkRepositoryUpdateRequest(
                chunk_id=request.chunk_id,
                payload=request.payload,
            )
        )
        if data is None:
            raise ResourceNotFoundError()
        return DocumentChunkResponse(data=data)

    async def delete(self, request: DocumentChunkDeleteRequest) -> DocumentChunkResponse:
        data = await self.repository.delete(
            DocumentChunkRepositoryDeleteRequest(chunk_id=request.chunk_id)
        )
        if data is None:
            raise ResourceNotFoundError()
        return DocumentChunkResponse(data=data)
