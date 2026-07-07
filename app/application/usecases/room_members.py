from app.core.exceptions import ResourceNotFoundError
from app.domain.interfaces import RoomMemberRepository
from app.domain.schemas.crud import CrudItemResponse
from app.domain.schemas.resources.rooms import (
    AddRoomMemberRequest,
    RoomMemberPath,
    RoomMemberRepositoryCreateRequest,
    RoomMemberRepositoryDeleteRequest,
)


class RoomMemberUseCase:
    def __init__(self, repository: RoomMemberRepository) -> None:
        self.repository = repository

    async def add(self, room_id: str, request: AddRoomMemberRequest) -> CrudItemResponse:
        data = await self.repository.create(
            RoomMemberRepositoryCreateRequest(
                room_id=room_id,
                member_id=request.member_id,
                role=request.role,
            )
        )
        return CrudItemResponse(data=data)

    async def remove(self, request: RoomMemberPath) -> CrudItemResponse:
        data = await self.repository.delete(
            RoomMemberRepositoryDeleteRequest(
                room_id=request.room_id,
                member_id=request.member_id,
            )
        )
        if data is None:
            raise ResourceNotFoundError()
        return CrudItemResponse(data=data)
