from app.domain.schemas.resources.notebooks import (
    NotebookRepositoryCreateRequest,
    NotebookRepositoryDeleteRequest,
    NotebookRepositoryGetRequest,
    NotebookRepositoryListRequest,
    NotebookRepositoryUpdateRequest,
    NotebookTagRepositoryCreateRequest,
    NotebookTagRepositoryDeleteRequest,
)
from app.infra.repositories.base import BaseSupabaseRepository


class NotebookRepository(BaseSupabaseRepository):
    table_name = "notebooks"
    id_field = "notebook_id"

    async def list(self, request: NotebookRepositoryListRequest) -> list[dict]:
        return await self._list(self.table_name, request.limit, request.offset)

    async def get(self, request: NotebookRepositoryGetRequest) -> dict | None:
        return await self._get(self.table_name, self.id_field, str(request.notebook_id))

    async def create(self, request: NotebookRepositoryCreateRequest) -> dict:
        payload = request.payload.model_dump(exclude_unset=True, mode="json")
        return await self._create(self.table_name, payload)

    async def update(self, request: NotebookRepositoryUpdateRequest) -> dict | None:
        payload = request.payload.model_dump(exclude_unset=True, mode="json")
        payload["updated_at"] = request.updated_at.isoformat()
        return await self._update(
            self.table_name, self.id_field, str(request.notebook_id), payload
        )

    async def delete(self, request: NotebookRepositoryDeleteRequest) -> dict | None:
        return await self._delete(self.table_name, self.id_field, str(request.notebook_id))


class NotebookTagRepository(BaseSupabaseRepository):
    table_name = "notebook_tags"

    async def create(self, request: NotebookTagRepositoryCreateRequest) -> dict:
        return await self._create(self.table_name, request.model_dump(mode="json"))

    async def delete(self, request: NotebookTagRepositoryDeleteRequest) -> dict | None:
        return await self._delete_by_filter(self.table_name, request.model_dump(mode="json"))
