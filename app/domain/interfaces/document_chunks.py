from typing import Protocol

from app.domain.schemas.resources.document_chunks import (
    DocumentChunkRepositoryCreateRequest,
    DocumentChunkRepositoryDeleteRequest,
    DocumentChunkRepositoryGetRequest,
    DocumentChunkRepositoryListRequest,
    DocumentChunkRepositoryUpdateRequest,
)


class DocumentChunkRepository(Protocol):
    async def list(self, request: DocumentChunkRepositoryListRequest) -> list[dict]:
        raise NotImplementedError

    async def get(self, request: DocumentChunkRepositoryGetRequest) -> dict | None:
        raise NotImplementedError

    async def create(self, request: DocumentChunkRepositoryCreateRequest) -> dict:
        raise NotImplementedError

    async def update(self, request: DocumentChunkRepositoryUpdateRequest) -> dict | None:
        raise NotImplementedError

    async def delete(self, request: DocumentChunkRepositoryDeleteRequest) -> dict | None:
        raise NotImplementedError
