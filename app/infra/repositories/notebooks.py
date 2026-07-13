from app.domain.schemas.resources.notebooks import (
    NotebookRepositoryCreateRequest,
    NotebookRepositoryDeleteRequest,
    NotebookRepositoryGetRequest,
    NotebookRepositoryListRequest,
    NotebookRepositoryUpdateRequest,
    NotebookTagRepositoryCreateRequest,
    NotebookTagRepositoryDeleteRequest,
)
from app.core.exceptions import RepositoryError, ResourceNotFoundError
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
        params = {f"p_{key}": value for key, value in payload.items()}
        return await self._rpc_first("create_personal_notebook", params, "crear")

    async def update(self, request: NotebookRepositoryUpdateRequest) -> dict | None:
        payload = request.payload.model_dump(exclude_unset=True, mode="json")
        payload["updated_at"] = request.updated_at.isoformat()
        return await self._update(self.table_name, self.id_field, str(request.notebook_id), payload)

    async def delete(self, request: NotebookRepositoryDeleteRequest) -> dict | None:
        return await self._delete(self.table_name, self.id_field, str(request.notebook_id))


class NotebookTagRepository(BaseSupabaseRepository):
    table_name = "notebook_tags"

    async def create(self, request: NotebookTagRepositoryCreateRequest) -> dict:
        payload = request.model_dump(mode="json")
        try:
            response = await self._execute(self.client.table(self.table_name).insert(payload))
        except Exception as exc:
            code = getattr(exc, "code", None)
            if code == "23505":
                # The relationship already exists. Treat retries as idempotent.
                return payload
            if code in {"23503", "42501"}:
                # Do not reveal whether the notebook/tag exists when RLS denies it.
                raise ResourceNotFoundError() from exc
            raise RepositoryError("crear") from exc
        return self._first(response.data) or payload

    async def delete(self, request: NotebookTagRepositoryDeleteRequest) -> dict | None:
        return await self._delete_by_filter(self.table_name, request.model_dump(mode="json"))
