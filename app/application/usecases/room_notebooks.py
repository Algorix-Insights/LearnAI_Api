from app.core.exceptions import ResourceNotFoundError
from app.domain.interfaces import RoomNotebookRepository
from app.domain.schemas.crud import CrudItemResponse
from app.domain.schemas.resources.rooms import (
    AddRoomNotebookRequest,
    RoomNotebookPath,
    RoomNotebookRepositoryCreateRequest,
    RoomNotebookRepositoryDeleteRequest,
)


class RoomNotebookUseCase:
    def __init__(self, repository: RoomNotebookRepository) -> None:
        self.repository = repository

    async def add(self, room_id: str, request: AddRoomNotebookRequest) -> CrudItemResponse:
        data = await self.repository.create(
            RoomNotebookRepositoryCreateRequest(
                room_id=room_id,
                notebook_id=request.notebook_id,
                created_by=request.created_by,
            )
        )
        return CrudItemResponse(data=data)

    async def remove(self, request: RoomNotebookPath) -> CrudItemResponse:
        data = await self.repository.delete(
            RoomNotebookRepositoryDeleteRequest(
                room_id=request.room_id,
                notebook_id=request.notebook_id,
            )
        )
        if data is None:
            raise ResourceNotFoundError()
        return CrudItemResponse(data=data)
