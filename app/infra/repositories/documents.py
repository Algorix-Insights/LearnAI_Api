from app.domain.schemas.resources.documents import (
    DocumentRepositoryCreateRequest,
    DocumentRepositoryDeleteRequest,
    DocumentRepositoryGetRequest,
    DocumentRepositoryListRequest,
    DocumentRepositoryUpdateRequest,
)
from app.infra.repositories.base import BaseSupabaseRepository


class DocumentRepository(BaseSupabaseRepository):
    table_name = "documents"
    id_field = "document_id"

    async def list(self, request: DocumentRepositoryListRequest) -> list[dict]:
        return await self._list(self.table_name, request.limit, request.offset)

    async def get(self, request: DocumentRepositoryGetRequest) -> dict | None:
        return await self._get(self.table_name, self.id_field, str(request.document_id))

    async def create(self, request: DocumentRepositoryCreateRequest) -> dict:
        payload = request.payload.model_dump(exclude_unset=True, mode="json")
        return await self._create(self.table_name, payload)

    async def update(self, request: DocumentRepositoryUpdateRequest) -> dict | None:
        payload = request.payload.model_dump(exclude_unset=True, mode="json")
        payload["updated_at"] = request.updated_at.isoformat()
        return await self._update(
            self.table_name, self.id_field, str(request.document_id), payload
        )

    async def delete(self, request: DocumentRepositoryDeleteRequest) -> dict | None:
        return await self._delete(self.table_name, self.id_field, str(request.document_id))
