from app.domain.schemas.resources.attempts import (
    AttemptRepositoryCreateRequest,
    AttemptRepositoryDeleteRequest,
    AttemptRepositoryGetRequest,
    AttemptRepositoryListRequest,
    AttemptRepositoryUpdateRequest,
)
from app.infra.repositories.base import BaseSupabaseRepository


class AttemptRepository(BaseSupabaseRepository):
    table_name = "attempts"
    id_field = "attempt_id"

    async def list(self, request: AttemptRepositoryListRequest) -> list[dict]:
        return await self._list(self.table_name, request.limit, request.offset)

    async def get(self, request: AttemptRepositoryGetRequest) -> dict | None:
        return await self._get(self.table_name, self.id_field, str(request.attempt_id))

    async def create(self, request: AttemptRepositoryCreateRequest) -> dict:
        payload = request.payload.model_dump(exclude_unset=True, mode="json")
        return await self._create(self.table_name, payload)

    async def update(self, request: AttemptRepositoryUpdateRequest) -> dict | None:
        payload = request.payload.model_dump(exclude_unset=True, mode="json")
        return await self._update(self.table_name, self.id_field, str(request.attempt_id), payload)

    async def delete(self, request: AttemptRepositoryDeleteRequest) -> dict | None:
        return await self._delete(self.table_name, self.id_field, str(request.attempt_id))
