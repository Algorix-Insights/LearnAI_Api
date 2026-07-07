from typing import Any

from supabase import Client

from app.core.exceptions import RepositoryError
from app.infra.db.supabase import get_supabase_client


class BaseSupabaseRepository:
    def __init__(self, client: Client | None = None) -> None:
        self.client = client or get_supabase_client()

    async def _list(self, table_name: str, limit: int, offset: int) -> list[dict[str, Any]]:
        try:
            response = (
                self.client.table(table_name)
                .select("*")
                .range(offset, offset + limit - 1)
                .execute()
            )
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
