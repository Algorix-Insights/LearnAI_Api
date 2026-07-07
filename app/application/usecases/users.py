from datetime import UTC, datetime

from app.core.exceptions import ResourceNotFoundError
from app.domain.interfaces import UserRepository
from app.domain.services import UserService
from app.domain.schemas.resources.users import (
    UserCreateRequest,
    UserDeleteRequest,
    UserListResponse,
    UserListRequest,
    UserPath,
    UserRepositoryCreateRequest,
    UserRepositoryDeleteRequest,
    UserRepositoryGetRequest,
    UserRepositoryListRequest,
    UserRepositoryUpdateRequest,
    UserResponse,
    UserUpdateRequest,
)


class UserUseCase:
    def __init__(self, repository: UserRepository, service: UserService | None = None) -> None:
        self.repository = repository
        self.service = service or UserService()

    async def list(self, request: UserListRequest) -> UserListResponse:
        data = await self.repository.list(
            UserRepositoryListRequest(limit=request.limit, offset=request.offset)
        )
        return UserListResponse(
            data=[self._hide_sensitive_fields(item) for item in data],
            limit=request.limit,
            offset=request.offset,
        )

    async def get(self, request: UserPath) -> UserResponse:
        data = await self.repository.get(UserRepositoryGetRequest(user_id=request.user_id))
        if data is None:
            raise ResourceNotFoundError()
        return UserResponse(data=self._hide_sensitive_fields(data))

    async def create(self, request: UserCreateRequest) -> UserResponse:
        request = self.service.prepare_create(request)
        data = await self.repository.create(UserRepositoryCreateRequest(payload=request.payload))
        return UserResponse(data=self._hide_sensitive_fields(data))

    async def update(self, request: UserUpdateRequest) -> UserResponse:
        request = self.service.prepare_update(request)
        data = await self.repository.update(
            UserRepositoryUpdateRequest(
                user_id=request.user_id,
                payload=request.payload,
                updated_at=datetime.now(UTC),
            )
        )
        if data is None:
            raise ResourceNotFoundError()
        return UserResponse(data=self._hide_sensitive_fields(data))

    async def delete(self, request: UserDeleteRequest) -> UserResponse:
        data = await self.repository.delete(UserRepositoryDeleteRequest(user_id=request.user_id))
        if data is None:
            raise ResourceNotFoundError()
        return UserResponse(data=self._hide_sensitive_fields(data))

    def _hide_sensitive_fields(self, item: dict) -> dict:
        return {key: value for key, value in item.items() if key != "hash_password"}
