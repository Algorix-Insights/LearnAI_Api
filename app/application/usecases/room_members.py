from app.core.exceptions import ResourceNotFoundError
from app.domain.interfaces import RoomMemberRepository
from app.domain.schemas.resources.rooms import (
    AddRoomMemberRequest,
    RoomMemberPath,
    RoomMemberRepositoryCreateRequest,
    RoomMemberRepositoryDeleteRequest,
    RoomMemberResponse,
)


class RoomMemberUseCase:
    def __init__(self, repository: RoomMemberRepository) -> None:
        self.repository = repository

    async def add(self, room_id: str, request: AddRoomMemberRequest) -> RoomMemberResponse:
        data = await self.repository.create(
            RoomMemberRepositoryCreateRequest(
                room_id=room_id,
                member_id=request.member_id,
                role=request.role,
            )
        )
        return RoomMemberResponse(data=data)

    async def remove(self, request: RoomMemberPath) -> RoomMemberResponse:
        data = await self.repository.delete(
            RoomMemberRepositoryDeleteRequest(
                room_id=request.room_id,
                member_id=request.member_id,
            )
        )
        if data is None:
            raise ResourceNotFoundError()
        return RoomMemberResponse(data=data)
