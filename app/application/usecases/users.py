from datetime import UTC, datetime

from app.core.exceptions import EmptyPayloadError, ResourceNotFoundError
from app.domain.interfaces import UserRepository
from app.domain.schemas.crud import CrudItemResponse, CrudListResponse
from app.domain.schemas.resources.users import (
    UserCreateRequest,
    UserDeleteRequest,
    UserListRequest,
    UserPath,
    UserRepositoryCreateRequest,
    UserRepositoryDeleteRequest,
    UserRepositoryGetRequest,
    UserRepositoryListRequest,
    UserRepositoryUpdateRequest,
    UserUpdateRequest,
)


class UserUseCase:
    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    async def list(self, request: UserListRequest) -> CrudListResponse:
        data = await self.repository.list(
            UserRepositoryListRequest(limit=request.limit, offset=request.offset)
        )
        return CrudListResponse(
            data=[self._hide_sensitive_fields(item) for item in data],
            limit=request.limit,
            offset=request.offset,
        )

    async def get(self, request: UserPath) -> CrudItemResponse:
        data = await self.repository.get(UserRepositoryGetRequest(user_id=request.user_id))
        if data is None:
            raise ResourceNotFoundError()
        return CrudItemResponse(data=self._hide_sensitive_fields(data))

    async def create(self, request: UserCreateRequest) -> CrudItemResponse:
        data = await self.repository.create(UserRepositoryCreateRequest(payload=request.payload))
        return CrudItemResponse(data=self._hide_sensitive_fields(data))

    async def update(self, request: UserUpdateRequest) -> CrudItemResponse:
        if not request.payload.model_dump(exclude_unset=True):
            raise EmptyPayloadError()
        data = await self.repository.update(
            UserRepositoryUpdateRequest(
                user_id=request.user_id,
                payload=request.payload,
                updated_at=datetime.now(UTC),
            )
        )
        if data is None:
            raise ResourceNotFoundError()
        return CrudItemResponse(data=self._hide_sensitive_fields(data))

    async def delete(self, request: UserDeleteRequest) -> CrudItemResponse:
        data = await self.repository.delete(UserRepositoryDeleteRequest(user_id=request.user_id))
        if data is None:
            raise ResourceNotFoundError()
        return CrudItemResponse(data=self._hide_sensitive_fields(data))

    def _hide_sensitive_fields(self, item: dict) -> dict:
        return {key: value for key, value in item.items() if key != "hash_password"}
