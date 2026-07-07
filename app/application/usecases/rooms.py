from datetime import UTC, datetime

from app.core.exceptions import EmptyPayloadError, ResourceNotFoundError
from app.domain.interfaces import RoomRepository
from app.domain.schemas.resources.rooms import (
    RoomCreateRequest,
    RoomDeleteRequest,
    RoomListResponse,
    RoomListRequest,
    RoomPath,
    RoomRepositoryCreateRequest,
    RoomRepositoryDeleteRequest,
    RoomRepositoryGetRequest,
    RoomRepositoryListRequest,
    RoomRepositoryUpdateRequest,
    RoomResponse,
    RoomUpdateRequest,
)


class RoomUseCase:
    def __init__(self, repository: RoomRepository) -> None:
        self.repository = repository

    async def list(self, request: RoomListRequest) -> RoomListResponse:
        data = await self.repository.list(
            RoomRepositoryListRequest(limit=request.limit, offset=request.offset)
        )
        return RoomListResponse(data=data, limit=request.limit, offset=request.offset)

    async def get(self, request: RoomPath) -> RoomResponse:
        data = await self.repository.get(RoomRepositoryGetRequest(room_id=request.room_id))
        if data is None:
            raise ResourceNotFoundError()
        return RoomResponse(data=data)

    async def create(self, request: RoomCreateRequest) -> RoomResponse:
        data = await self.repository.create(RoomRepositoryCreateRequest(payload=request.payload))
        return RoomResponse(data=data)

    async def update(self, request: RoomUpdateRequest) -> RoomResponse:
        if not request.payload.model_dump(exclude_unset=True):
            raise EmptyPayloadError()
        data = await self.repository.update(
            RoomRepositoryUpdateRequest(
                room_id=request.room_id,
                payload=request.payload,
                updated_at=datetime.now(UTC),
            )
        )
        if data is None:
            raise ResourceNotFoundError()
        return RoomResponse(data=data)

    async def delete(self, request: RoomDeleteRequest) -> RoomResponse:
        data = await self.repository.delete(RoomRepositoryDeleteRequest(room_id=request.room_id))
        if data is None:
            raise ResourceNotFoundError()
        return RoomResponse(data=data)
