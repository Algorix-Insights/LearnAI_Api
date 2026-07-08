from typing import Any

from supabase import Client

from app.core.exceptions import RepositoryError
from app.core.query import ApiFilter, get_api_query_params
from app.infra.db.supabase import get_supabase_client


class BaseSupabaseRepository:
    def __init__(self, client: Client | None = None) -> None:
        self.client = client or get_supabase_client()

    async def _list(self, table_name: str, limit: int, offset: int) -> list[dict[str, Any]]:
        try:
            api_query = get_api_query_params()
            if api_query is not None:
                limit = api_query.limit
                offset = api_query.offset

            response = (
                self.client.table(table_name)
                .select("*")
            )
            for item_filter in api_query.filters if api_query is not None else ():
                response = self._apply_filter(response, item_filter)
            response = response.range(offset, offset + limit - 1).execute()
        except Exception as exc:
            raise RepositoryError("listar") from exc
        return response.data or []

    async def _get(self, table_name: str, id_field: str, item_id: str) -> dict[str, Any] | None:
        try:
            response = (
                self.client.table(table_name)
                .select("*")
                .eq(id_field, item_id)
                .limit(1)
                .execute()
            )
        except Exception as exc:
            raise RepositoryError("consultar") from exc
        return self._first(response.data)

    async def _create(self, table_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            response = self.client.table(table_name).insert(payload).execute()
        except Exception as exc:
            raise RepositoryError("crear") from exc
        return self._first(response.data) or {}

    async def _update(
        self,
        table_name: str,
        id_field: str,
        item_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any] | None:
        try:
            response = (
                self.client.table(table_name)
                .update(payload)
                .eq(id_field, item_id)
                .execute()
            )
        except Exception as exc:
            raise RepositoryError("actualizar") from exc
        return self._first(response.data)

    async def _delete(
        self, table_name: str, id_field: str, item_id: str
    ) -> dict[str, Any] | None:
        try:
            response = (
                self.client.table(table_name)
                .delete()
                .eq(id_field, item_id)
                .execute()
            )
        except Exception as exc:
            raise RepositoryError("eliminar") from exc
        return self._first(response.data)

    async def _delete_by_filter(
        self, table_name: str, filters: dict[str, Any]
    ) -> dict[str, Any] | None:
        try:
            query = self.client.table(table_name).delete()
            for field, value in filters.items():
                query = query.eq(field, value)
            response = query.execute()
        except Exception as exc:
            raise RepositoryError("eliminar") from exc
        return self._first(response.data)

    def _first(self, data: list[dict[str, Any]] | None) -> dict[str, Any] | None:
        if not data:
            return None
        return data[0]

    def _apply_filter(self, query: Any, item_filter: ApiFilter) -> Any:
        field = item_filter.field
        value = item_filter.value
        match item_filter.operator:
            case "eq":
                return query.eq(field, value)
            case "neq":
                return query.neq(field, value)
            case "gt":
                return query.gt(field, value)
            case "gte":
                return query.gte(field, value)
            case "lt":
                return query.lt(field, value)
            case "lte":
                return query.lte(field, value)
            case "like":
                return query.like(field, value)
            case "ilike":
                return query.ilike(field, value)
            case "in":
                return query.in_(field, value)
            case "is":
                return query.is_(field, value)
        return query
