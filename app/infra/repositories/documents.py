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

    async def get_by_hash(self, *, notebook_id: str, content_hash: str) -> dict | None:
        try:
            response = (
                self.client.table(self.table_name)
                .select("*")
                .eq("notebook_id", notebook_id)
                .eq("content_hash", content_hash)
                .limit(1)
                .execute()
            )
        except Exception as exc:
            from app.core.exceptions import RepositoryError

            raise RepositoryError("consultar") from exc
        return self._first(response.data)

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
