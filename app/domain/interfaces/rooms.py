from typing import Protocol

from app.domain.schemas.resources.rooms import (
    RoomMemberRepositoryCreateRequest,
    RoomMemberRepositoryDeleteRequest,
    RoomNotebookRepositoryCreateRequest,
    RoomNotebookRepositoryDeleteRequest,
    RoomRepositoryCreateRequest,
    RoomRepositoryDeleteRequest,
    RoomRepositoryGetRequest,
    RoomRepositoryListRequest,
    RoomRepositoryUpdateRequest,
)


class RoomRepository(Protocol):
    async def list(self, request: RoomRepositoryListRequest) -> list[dict]:
        raise NotImplementedError

    async def get(self, request: RoomRepositoryGetRequest) -> dict | None:
        raise NotImplementedError

    async def create(self, request: RoomRepositoryCreateRequest) -> dict:
        raise NotImplementedError

    async def update(self, request: RoomRepositoryUpdateRequest) -> dict | None:
        raise NotImplementedError

    async def delete(self, request: RoomRepositoryDeleteRequest) -> dict | None:
        raise NotImplementedError


class RoomMemberRepository(Protocol):
    async def create(self, request: RoomMemberRepositoryCreateRequest) -> dict:
        raise NotImplementedError

    async def delete(self, request: RoomMemberRepositoryDeleteRequest) -> dict | None:
        raise NotImplementedError


class RoomNotebookRepository(Protocol):
    async def create(self, request: RoomNotebookRepositoryCreateRequest) -> dict:
        raise NotImplementedError

    async def delete(self, request: RoomNotebookRepositoryDeleteRequest) -> dict | None:
        raise NotImplementedError
