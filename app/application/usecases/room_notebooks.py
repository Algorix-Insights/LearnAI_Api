from typing import Any

from app.core.exceptions import ResourceNotFoundError
from app.domain.interfaces import CompositeRepository
from app.domain.schemas import AddRoomNotebookRequest, RoomNotebookPath
from app.domain.schemas.aggregate import RepositoryCreateItemRequest, RepositoryFilterRequest
from app.domain.schemas.crud import CrudItemResponse


class RoomNotebookUseCase:
    def __init__(self, repository: CompositeRepository) -> None:
        self.repository = repository

    async def add(self, room_id: str, request: AddRoomNotebookRequest) -> CrudItemResponse:
        payload: dict[str, Any] = {"room_id": room_id, **request.model_dump(mode="json")}
        data = await self.repository.create(RepositoryCreateItemRequest(payload=payload))
        return CrudItemResponse(data=data)

    async def remove(self, request: RoomNotebookPath) -> CrudItemResponse:
        data = await self.repository.delete_by_filter(
            RepositoryFilterRequest(filters=request.model_dump(mode="json"))
        )
        if data is None:
            raise ResourceNotFoundError()
        return CrudItemResponse(data=data)
