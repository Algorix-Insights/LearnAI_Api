from typing import Protocol

from app.domain.schemas.aggregate import (
    RepositoryCreateItemRequest,
    RepositoryFilterRequest,
    RepositoryItemRequest,
    RepositoryListItemsRequest,
    RepositoryUpdateByFilterRequest,
    RepositoryUpdateItemRequest,
)


class AggregateRepository(Protocol):
    async def list(self, request: RepositoryListItemsRequest) -> list[dict]:
        raise NotImplementedError

    async def get(self, request: RepositoryItemRequest) -> dict | None:
        raise NotImplementedError

    async def create(self, request: RepositoryCreateItemRequest) -> dict:
        raise NotImplementedError

    async def update(self, request: RepositoryUpdateItemRequest) -> dict | None:
        raise NotImplementedError

    async def delete(self, request: RepositoryItemRequest) -> dict | None:
        raise NotImplementedError


class CompositeRepository(Protocol):
    async def get_by_filter(self, request: RepositoryFilterRequest) -> dict | None:
        raise NotImplementedError

    async def create(self, request: RepositoryCreateItemRequest) -> dict:
        raise NotImplementedError

    async def update_by_filter(self, request: RepositoryUpdateByFilterRequest) -> dict | None:
        raise NotImplementedError

    async def delete_by_filter(self, request: RepositoryFilterRequest) -> dict | None:
        raise NotImplementedError
