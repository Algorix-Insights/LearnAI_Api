from typing import Protocol

from app.domain.schemas.resources.documents import (
    DocumentRepositoryCreateRequest,
    DocumentRepositoryDeleteRequest,
    DocumentRepositoryGetRequest,
    DocumentRepositoryListRequest,
    DocumentRepositoryUpdateRequest,
)


class DocumentRepository(Protocol):
    async def list(self, request: DocumentRepositoryListRequest) -> list[dict]:
        raise NotImplementedError

    async def get(self, request: DocumentRepositoryGetRequest) -> dict | None:
        raise NotImplementedError

    async def create(self, request: DocumentRepositoryCreateRequest) -> dict:
        raise NotImplementedError

    async def update(self, request: DocumentRepositoryUpdateRequest) -> dict | None:
        raise NotImplementedError

    async def delete(self, request: DocumentRepositoryDeleteRequest) -> dict | None:
        raise NotImplementedError
