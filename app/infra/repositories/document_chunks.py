from __future__ import annotations

from app.domain.schemas.resources.document_chunks import (
    DocumentChunkRepositoryCreateRequest,
    DocumentChunkRepositoryDeleteRequest,
    DocumentChunkRepositoryGetRequest,
    DocumentChunkRepositoryListRequest,
    DocumentChunkRepositoryUpdateRequest,
)
from app.core.exceptions import RepositoryError
from app.infra.repositories.base import BaseSupabaseRepository


class DocumentChunkRepository(BaseSupabaseRepository):
    table_name = "document_chunks"
    id_field = "chunk_id"
    safe_columns = (
        "chunk_id,document_id,chunk_index,content,model,token_count,created_at"
    )

    async def list(self, request: DocumentChunkRepositoryListRequest) -> list[dict]:
        return await self._list(
            self.table_name,
            request.limit,
            request.offset,
            columns=self.safe_columns,
        )

    async def get(self, request: DocumentChunkRepositoryGetRequest) -> dict | None:
        return await self._get(
            self.table_name,
            self.id_field,
            str(request.chunk_id),
            columns=self.safe_columns,
        )

    async def create(self, request: DocumentChunkRepositoryCreateRequest) -> dict:
        payload = request.payload.model_dump(exclude_unset=True, mode="json")
        return await self._create(self.table_name, payload)

    async def create_many(self, payloads: list[dict]) -> list[dict]:
        try:
            response = await self._execute(
                self.client.table(self.table_name).insert(payloads)
            )
        except Exception as exc:
            raise RepositoryError("crear") from exc
        return response.data or []

    async def delete_for_document(self, document_id: str) -> list[dict]:
        try:
            query = (
                self.client.table(self.table_name)
                .delete()
                .eq("document_id", document_id)
            )
            response = await self._execute(query)
        except Exception as exc:
            raise RepositoryError("eliminar") from exc
        return response.data or []

    async def count_for_document(self, document_id: str) -> int:
        try:
            query = (
                self.client.table(self.table_name)
                .select("chunk_id")
                .eq("document_id", document_id)
            )
            response = await self._execute(query)
        except Exception as exc:
            raise RepositoryError("contar") from exc
        return len(response.data or [])

    async def update(self, request: DocumentChunkRepositoryUpdateRequest) -> dict | None:
        payload = request.payload.model_dump(exclude_unset=True, mode="json")
        return await self._update(self.table_name, self.id_field, str(request.chunk_id), payload)

    async def delete(self, request: DocumentChunkRepositoryDeleteRequest) -> dict | None:
        return await self._delete(self.table_name, self.id_field, str(request.chunk_id))
