from app.domain.schemas.resources.rooms import (
    RoomMemberRepositoryCreateRequest,
    RoomMemberRepositoryDeleteRequest,
    RoomNotebookRepositoryCreateRequest,
    RoomNotebookRepositoryDeleteRequest,
    RoomRepositoryCreateRequest,
    RoomRepositoryDeleteRequest,
    RoomRepositoryGetRequest,
    RoomRepositoryListRequest,
    RoomRepositoryUpdateRequest,
)
from app.infra.repositories.base import BaseSupabaseRepository


class RoomRepository(BaseSupabaseRepository):
    table_name = "rooms"
    id_field = "room_id"

    async def list(self, request: RoomRepositoryListRequest) -> list[dict]:
        return await self._list(self.table_name, request.limit, request.offset)

    async def get(self, request: RoomRepositoryGetRequest) -> dict | None:
        return await self._get(self.table_name, self.id_field, str(request.room_id))

    async def create(self, request: RoomRepositoryCreateRequest) -> dict:
        payload = request.payload.model_dump(exclude_unset=True, mode="json")
        return await self._create(self.table_name, payload)

    async def update(self, request: RoomRepositoryUpdateRequest) -> dict | None:
        payload = request.payload.model_dump(exclude_unset=True, mode="json")
        payload["updated_at"] = request.updated_at.isoformat()
        return await self._update(self.table_name, self.id_field, str(request.room_id), payload)

    async def delete(self, request: RoomRepositoryDeleteRequest) -> dict | None:
        return await self._delete(self.table_name, self.id_field, str(request.room_id))


class MemberRoomRepository(BaseSupabaseRepository):
    table_name = "members_rooms"

    async def create(self, request: RoomMemberRepositoryCreateRequest) -> dict:
        return await self._create(self.table_name, request.model_dump(mode="json"))

    async def delete(self, request: RoomMemberRepositoryDeleteRequest) -> dict | None:
        return await self._delete_by_filter(self.table_name, request.model_dump(mode="json"))


class RoomNotebookRepository(BaseSupabaseRepository):
    table_name = "room_notebooks"

    async def create(self, request: RoomNotebookRepositoryCreateRequest) -> dict:
        return await self._create(self.table_name, request.model_dump(mode="json"))

    async def delete(self, request: RoomNotebookRepositoryDeleteRequest) -> dict | None:
        return await self._delete_by_filter(self.table_name, request.model_dump(mode="json"))
