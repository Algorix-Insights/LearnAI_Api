from typing import Protocol

from app.domain.schemas.resources.notebooks import (
    NotebookRepositoryCreateRequest,
    NotebookRepositoryDeleteRequest,
    NotebookRepositoryGetRequest,
    NotebookRepositoryListRequest,
    NotebookRepositoryUpdateRequest,
    NotebookTagRepositoryCreateRequest,
    NotebookTagRepositoryDeleteRequest,
)


class NotebookRepository(Protocol):
    async def list(self, request: NotebookRepositoryListRequest) -> list[dict]:
        raise NotImplementedError

    async def get(self, request: NotebookRepositoryGetRequest) -> dict | None:
        raise NotImplementedError

    async def create(self, request: NotebookRepositoryCreateRequest) -> dict:
        raise NotImplementedError

    async def update(self, request: NotebookRepositoryUpdateRequest) -> dict | None:
        raise NotImplementedError

    async def delete(self, request: NotebookRepositoryDeleteRequest) -> dict | None:
        raise NotImplementedError


class NotebookTagRepository(Protocol):
    async def create(self, request: NotebookTagRepositoryCreateRequest) -> dict:
        raise NotImplementedError

    async def delete(self, request: NotebookTagRepositoryDeleteRequest) -> dict | None:
        raise NotImplementedError
