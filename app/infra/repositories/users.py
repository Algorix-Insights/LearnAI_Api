from app.domain.schemas.resources.users import (
    PersonalNotebookRepositoryCreateRequest,
    PersonalNotebookRepositoryDeleteRequest,
    UserRepositoryCreateRequest,
    UserRepositoryDeleteRequest,
    UserRepositoryGetRequest,
    UserRepositoryListRequest,
    UserRepositoryUpdateRequest,
)
from app.infra.repositories.base import BaseSupabaseRepository


class UserRepository(BaseSupabaseRepository):
    table_name = "users"
    id_field = "user_id"

    async def list(self, request: UserRepositoryListRequest) -> list[dict]:
        return await self._list(self.table_name, request.limit, request.offset)

    async def get(self, request: UserRepositoryGetRequest) -> dict | None:
        return await self._get(self.table_name, self.id_field, str(request.user_id))

    async def create(self, request: UserRepositoryCreateRequest) -> dict:
        payload = request.payload.model_dump(exclude_unset=True, mode="json")
        return await self._create(self.table_name, payload)

    async def update(self, request: UserRepositoryUpdateRequest) -> dict | None:
        payload = request.payload.model_dump(exclude_unset=True, mode="json")
        payload["updated_at"] = request.updated_at.isoformat()
        return await self._update(self.table_name, self.id_field, str(request.user_id), payload)

    async def delete(self, request: UserRepositoryDeleteRequest) -> dict | None:
        return await self._delete(self.table_name, self.id_field, str(request.user_id))


class PersonalNotebookRepository(BaseSupabaseRepository):
    table_name = "personal_notebooks"

    async def create(self, request: PersonalNotebookRepositoryCreateRequest) -> dict:
        return await self._create(self.table_name, request.model_dump(mode="json"))

    async def delete(self, request: PersonalNotebookRepositoryDeleteRequest) -> dict | None:
        return await self._delete_by_filter(self.table_name, request.model_dump(mode="json"))
