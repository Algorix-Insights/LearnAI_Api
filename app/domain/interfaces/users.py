from typing import Protocol

from app.domain.schemas.resources.users import (
    PersonalNotebookRepositoryCreateRequest,
    PersonalNotebookRepositoryDeleteRequest,
    UserRepositoryCreateRequest,
    UserRepositoryDeleteRequest,
    UserRepositoryGetRequest,
    UserRepositoryListRequest,
    UserRepositoryUpdateRequest,
)


class UserRepository(Protocol):
    async def list(self, request: UserRepositoryListRequest) -> list[dict]:
        raise NotImplementedError

    async def get(self, request: UserRepositoryGetRequest) -> dict | None:
        raise NotImplementedError

    async def create(self, request: UserRepositoryCreateRequest) -> dict:
        raise NotImplementedError

    async def update(self, request: UserRepositoryUpdateRequest) -> dict | None:
        raise NotImplementedError

    async def delete(self, request: UserRepositoryDeleteRequest) -> dict | None:
        raise NotImplementedError


class PersonalNotebookRepository(Protocol):
    async def create(self, request: PersonalNotebookRepositoryCreateRequest) -> dict:
        raise NotImplementedError

    async def delete(self, request: PersonalNotebookRepositoryDeleteRequest) -> dict | None:
        raise NotImplementedError
