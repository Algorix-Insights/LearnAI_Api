from typing import Any

from supabase import Client

from app.core.exceptions import RepositoryError
from app.domain.interfaces import AggregateRepository, CompositeRepository
from app.domain.schemas.aggregate import (
    RepositoryCreateItemRequest,
    RepositoryFilterRequest,
    RepositoryItemRequest,
    RepositoryListItemsRequest,
    RepositoryUpdateByFilterRequest,
    RepositoryUpdateItemRequest,
)
from app.infra.db.supabase import get_supabase_client


class BaseSupabaseAggregateRepository(AggregateRepository):
    table_name: str
    id_field: str

    def __init__(self, client: Client | None = None) -> None:
        self.client = client or get_supabase_client()

    async def list(self, request: RepositoryListItemsRequest) -> list[dict[str, Any]]:
        try:
            response = (
                self.client.table(self.table_name)
                .select("*")
                .range(request.offset, request.offset + request.limit - 1)
                .execute()
            )
        except Exception as exc:
            raise RepositoryError("listar") from exc
        return response.data or []

    async def get(self, request: RepositoryItemRequest) -> dict[str, Any] | None:
        try:
            response = (
                self.client.table(self.table_name)
                .select("*")
                .eq(self.id_field, request.item_id)
                .limit(1)
                .execute()
            )
        except Exception as exc:
            raise RepositoryError("consultar") from exc
        return self._first(response.data)

    async def create(self, request: RepositoryCreateItemRequest) -> dict[str, Any]:
        try:
            response = self.client.table(self.table_name).insert(request.payload).execute()
        except Exception as exc:
            raise RepositoryError("crear") from exc
        return self._first(response.data) or {}

    async def update(self, request: RepositoryUpdateItemRequest) -> dict[str, Any] | None:
        try:
            response = (
                self.client.table(self.table_name)
                .update(request.payload)
                .eq(self.id_field, request.item_id)
                .execute()
            )
        except Exception as exc:
            raise RepositoryError("actualizar") from exc
        return self._first(response.data)

    async def delete(self, request: RepositoryItemRequest) -> dict[str, Any] | None:
        try:
            response = (
                self.client.table(self.table_name)
                .delete()
                .eq(self.id_field, request.item_id)
                .execute()
            )
        except Exception as exc:
            raise RepositoryError("eliminar") from exc
        return self._first(response.data)

    def _first(self, data: list[dict[str, Any]] | None) -> dict[str, Any] | None:
        if not data:
            return None
        return data[0]


class BaseSupabaseCompositeRepository(CompositeRepository):
    table_name: str

    def __init__(self, client: Client | None = None) -> None:
        self.client = client or get_supabase_client()

    async def get_by_filter(self, request: RepositoryFilterRequest) -> dict[str, Any] | None:
        try:
            query = self.client.table(self.table_name).select("*")
            for field, value in request.filters.items():
                query = query.eq(field, value)
            response = query.limit(1).execute()
        except Exception as exc:
            raise RepositoryError("consultar") from exc
        return self._first(response.data)

    async def create(self, request: RepositoryCreateItemRequest) -> dict[str, Any]:
        try:
            response = self.client.table(self.table_name).insert(request.payload).execute()
        except Exception as exc:
            raise RepositoryError("crear") from exc
        return self._first(response.data) or {}

    async def update_by_filter(
        self, request: RepositoryUpdateByFilterRequest
    ) -> dict[str, Any] | None:
        try:
            query = self.client.table(self.table_name).update(request.payload)
            for field, value in request.filters.items():
                query = query.eq(field, value)
            response = query.execute()
        except Exception as exc:
            raise RepositoryError("actualizar") from exc
        return self._first(response.data)

    async def delete_by_filter(self, request: RepositoryFilterRequest) -> dict[str, Any] | None:
        try:
            query = self.client.table(self.table_name).delete()
            for field, value in request.filters.items():
                query = query.eq(field, value)
            response = query.execute()
        except Exception as exc:
            raise RepositoryError("eliminar") from exc
        return self._first(response.data)

    def _first(self, data: list[dict[str, Any]] | None) -> dict[str, Any] | None:
        if not data:
            return None
        return data[0]

