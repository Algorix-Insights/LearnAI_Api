from app.domain.schemas.resources.flashcards import (
    FlashcardRepositoryCreateRequest,
    FlashcardRepositoryDeleteRequest,
    FlashcardRepositoryGetRequest,
    FlashcardRepositoryListRequest,
    FlashcardRepositoryUpdateRequest,
)
from app.infra.repositories.base import BaseSupabaseRepository


class FlashcardRepository(BaseSupabaseRepository):
    table_name = "flashcards"
    id_field = "flashcard_id"

    async def list(self, request: FlashcardRepositoryListRequest) -> list[dict]:
        return await self._list(self.table_name, request.limit, request.offset)

    async def get(self, request: FlashcardRepositoryGetRequest) -> dict | None:
        return await self._get(self.table_name, self.id_field, str(request.flashcard_id))

    async def create(self, request: FlashcardRepositoryCreateRequest) -> dict:
        payload = request.payload.model_dump(exclude_unset=True, mode="json")
        return await self._create(self.table_name, payload)

    async def update(self, request: FlashcardRepositoryUpdateRequest) -> dict | None:
        payload = request.payload.model_dump(exclude_unset=True, mode="json")
        return await self._update(
            self.table_name, self.id_field, str(request.flashcard_id), payload
        )

    async def delete(self, request: FlashcardRepositoryDeleteRequest) -> dict | None:
        return await self._delete(self.table_name, self.id_field, str(request.flashcard_id))
