from typing import Protocol

from app.domain.schemas.resources.tags import (
    TagRepositoryCreateRequest,
    TagRepositoryDeleteRequest,
    TagRepositoryGetRequest,
    TagRepositoryListRequest,
    TagRepositoryUpdateRequest,
)


class TagRepository(Protocol):
    async def list(self, request: TagRepositoryListRequest) -> list[dict]:
        raise NotImplementedError

    async def get(self, request: TagRepositoryGetRequest) -> dict | None:
        raise NotImplementedError

    async def create(self, request: TagRepositoryCreateRequest) -> dict:
        raise NotImplementedError

    async def update(self, request: TagRepositoryUpdateRequest) -> dict | None:
        raise NotImplementedError

    async def delete(self, request: TagRepositoryDeleteRequest) -> dict | None:
        raise NotImplementedError
