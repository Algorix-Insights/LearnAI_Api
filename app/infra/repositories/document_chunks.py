from app.domain.schemas.resources.document_chunks import (
    DocumentChunkRepositoryCreateRequest,
    DocumentChunkRepositoryDeleteRequest,
    DocumentChunkRepositoryGetRequest,
    DocumentChunkRepositoryListRequest,
    DocumentChunkRepositoryUpdateRequest,
)
from app.infra.repositories.base import BaseSupabaseRepository


class DocumentChunkRepository(BaseSupabaseRepository):
    table_name = "document_chunks"
    id_field = "chunk_id"

    async def list(self, request: DocumentChunkRepositoryListRequest) -> list[dict]:
        return await self._list(self.table_name, request.limit, request.offset)

    async def get(self, request: DocumentChunkRepositoryGetRequest) -> dict | None:
        return await self._get(self.table_name, self.id_field, str(request.chunk_id))

    async def create(self, request: DocumentChunkRepositoryCreateRequest) -> dict:
        payload = request.payload.model_dump(exclude_unset=True, mode="json")
        return await self._create(self.table_name, payload)

    async def update(self, request: DocumentChunkRepositoryUpdateRequest) -> dict | None:
        payload = request.payload.model_dump(exclude_unset=True, mode="json")
        return await self._update(self.table_name, self.id_field, str(request.chunk_id), payload)

    async def delete(self, request: DocumentChunkRepositoryDeleteRequest) -> dict | None:
        return await self._delete(self.table_name, self.id_field, str(request.chunk_id))
