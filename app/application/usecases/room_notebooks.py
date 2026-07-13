from app.core.exceptions import ResourceNotFoundError
from app.domain.interfaces import RoomNotebookRepository
from app.domain.schemas.resources.rooms import (
    AddRoomNotebookRequest,
    RoomNotebookPath,
    RoomNotebookRepositoryCreateRequest,
    RoomNotebookRepositoryDeleteRequest,
    RoomNotebookResponse,
)


class RoomNotebookUseCase:
    def __init__(self, repository: RoomNotebookRepository) -> None:
        self.repository = repository

    async def add(self, room_id: str, request: AddRoomNotebookRequest) -> RoomNotebookResponse:
        data = await self.repository.create(
            RoomNotebookRepositoryCreateRequest(
                room_id=room_id,
                notebook_id=request.notebook_id,
            )
        )
        return RoomNotebookResponse(data=data)

    async def remove(self, request: RoomNotebookPath) -> RoomNotebookResponse:
        data = await self.repository.delete(
            RoomNotebookRepositoryDeleteRequest(
                room_id=request.room_id,
                notebook_id=request.notebook_id,
            )
        )
        if data is None:
            raise ResourceNotFoundError()
        return RoomNotebookResponse(data=data)
