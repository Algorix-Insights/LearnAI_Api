from typing import Protocol

from app.domain.schemas.resources.attempts import (
    AttemptRepositoryCreateRequest,
    AttemptRepositoryDeleteRequest,
    AttemptRepositoryGetRequest,
    AttemptRepositoryListRequest,
    AttemptRepositoryUpdateRequest,
)


class AttemptRepository(Protocol):
    async def list(self, request: AttemptRepositoryListRequest) -> list[dict]:
        raise NotImplementedError

    async def get(self, request: AttemptRepositoryGetRequest) -> dict | None:
        raise NotImplementedError

    async def create(self, request: AttemptRepositoryCreateRequest) -> dict:
        raise NotImplementedError

    async def update(self, request: AttemptRepositoryUpdateRequest) -> dict | None:
        raise NotImplementedError

    async def delete(self, request: AttemptRepositoryDeleteRequest) -> dict | None:
        raise NotImplementedError
