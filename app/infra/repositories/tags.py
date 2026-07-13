from uuid import UUID

from app.core.exceptions import ApiError, RepositoryError
from app.core.query import get_api_query_params
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
    internal_columns = "id,name,status,created_by_user_id"

    async def list(self, request: TagRepositoryListRequest) -> list[dict]:
        try:
            api_query = get_api_query_params()
            limit = api_query.limit if api_query is not None else request.limit
            offset = api_query.offset if api_query is not None else request.offset
            query = (
                self.client.table(self.table_name)
                .select(self.internal_columns)
                .or_(self._available_to_user_filter(request.user_id))
                .eq("status", "active")
            )
            for item_filter in api_query.filters if api_query is not None else ():
                query = self._apply_filter(query, item_filter)
            response = await self._execute(
                query.order("name").order("id").range(offset, offset + limit - 1)
            )
        except Exception as exc:
            raise RepositoryError("listar") from exc
        return [self._to_public(item) for item in response.data or []]

    async def get(self, request: TagRepositoryGetRequest) -> dict | None:
        try:
            response = await self._execute(
                self.client.table(self.table_name)
                .select(self.internal_columns)
                .eq(self.id_field, str(request.tag_id))
                .or_(self._available_to_user_filter(request.user_id))
                .eq("status", "active")
                .limit(1)
            )
        except Exception as exc:
            raise RepositoryError("consultar") from exc
        data = self._first(response.data)
        return self._to_public(data) if data is not None else None

    async def create(self, request: TagRepositoryCreateRequest) -> dict:
        payload = request.payload.model_dump(exclude_unset=True, mode="json")
        payload["created_by_user_id"] = str(request.user_id)
        try:
            response = await self._execute(
                self.client.table(self.table_name).insert(payload).select(self.internal_columns)
            )
        except Exception as exc:
            if self._is_unique_violation(exc):
                raise ApiError(409, "Ya existe una tag con ese nombre.") from exc
            raise RepositoryError("crear") from exc
        data = self._first(response.data)
        return self._to_public(data) if data is not None else {}

    async def update(self, request: TagRepositoryUpdateRequest) -> dict | None:
        payload = request.payload.model_dump(exclude_unset=True, mode="json")
        try:
            response = await self._execute(
                self.client.table(self.table_name)
                .update(payload)
                .eq(self.id_field, str(request.tag_id))
                .eq("created_by_user_id", str(request.user_id))
                .select(self.internal_columns)
            )
        except Exception as exc:
            if self._is_unique_violation(exc):
                raise ApiError(409, "Ya existe una tag con ese nombre.") from exc
            raise RepositoryError("actualizar") from exc
        data = self._first(response.data)
        return self._to_public(data) if data is not None else None

    async def delete(self, request: TagRepositoryDeleteRequest) -> dict | None:
        try:
            response = await self._execute(
                self.client.table(self.table_name)
                .delete()
                .eq(self.id_field, str(request.tag_id))
                .eq("created_by_user_id", str(request.user_id))
                .select(self.internal_columns)
            )
        except Exception as exc:
            raise RepositoryError("eliminar") from exc
        data = self._first(response.data)
        return self._to_public(data) if data is not None else None

    @staticmethod
    def _available_to_user_filter(user_id: UUID) -> str:
        return f"created_by_user_id.is.null,created_by_user_id.eq.{user_id}"

    @staticmethod
    def _to_public(item: dict) -> dict:
        public_item = dict(item)
        owner_id = public_item.pop("created_by_user_id", None)
        public_item["scope"] = "system" if owner_id is None else "user"
        return public_item

    @staticmethod
    def _is_unique_violation(exc: Exception) -> bool:
        return getattr(exc, "code", None) == "23505"
