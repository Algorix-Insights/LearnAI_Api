from app.core.exceptions import ResourceNotFoundError
from app.domain.interfaces import CompositeRepository
from app.domain.schemas import AddRoomMemberRequest, RoomMemberPath
from app.domain.schemas.aggregate import RepositoryCreateItemRequest, RepositoryFilterRequest
from app.domain.schemas.crud import CrudItemResponse


class RoomMemberUseCase:
    def __init__(self, repository: CompositeRepository) -> None:
        self.repository = repository

    async def add(self, room_id: str, request: AddRoomMemberRequest) -> CrudItemResponse:
        payload = {"room_id": room_id, **request.model_dump(mode="json")}
        data = await self.repository.create(RepositoryCreateItemRequest(payload=payload))
        return CrudItemResponse(data=data)

    async def remove(self, request: RoomMemberPath) -> CrudItemResponse:
        data = await self.repository.delete_by_filter(
            RepositoryFilterRequest(filters=request.model_dump(mode="json"))
        )
        if data is None:
            raise ResourceNotFoundError()
        return CrudItemResponse(data=data)
