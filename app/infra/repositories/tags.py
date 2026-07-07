from app.domain.schemas.resources.tags import (
    TagRepositoryCreateRequest,
    TagRepositoryDeleteRequest,
    TagRepositoryGetRequest,
    TagRepositoryListRequest,
    TagRepositoryUpdateRequest,
)
from app.infra.repositories.base import BaseSupabaseRepository


class TagRepository(BaseSupabaseRepository):
    table_name = "tags"
    id_field = "id"

    async def list(self, request: TagRepositoryListRequest) -> list[dict]:
        return await self._list(self.table_name, request.limit, request.offset)

    async def get(self, request: TagRepositoryGetRequest) -> dict | None:
        return await self._get(self.table_name, self.id_field, str(request.tag_id))

    async def create(self, request: TagRepositoryCreateRequest) -> dict:
        payload = request.payload.model_dump(exclude_unset=True, mode="json")
        return await self._create(self.table_name, payload)

    async def update(self, request: TagRepositoryUpdateRequest) -> dict | None:
        payload = request.payload.model_dump(exclude_unset=True, mode="json")
        return await self._update(self.table_name, self.id_field, str(request.tag_id), payload)

    async def delete(self, request: TagRepositoryDeleteRequest) -> dict | None:
        return await self._delete(self.table_name, self.id_field, str(request.tag_id))
