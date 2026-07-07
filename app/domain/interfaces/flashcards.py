from typing import Protocol

from app.domain.schemas.resources.flashcards import (
    FlashcardRepositoryCreateRequest,
    FlashcardRepositoryDeleteRequest,
    FlashcardRepositoryGetRequest,
    FlashcardRepositoryListRequest,
    FlashcardRepositoryUpdateRequest,
)


class FlashcardRepository(Protocol):
    async def list(self, request: FlashcardRepositoryListRequest) -> list[dict]:
        raise NotImplementedError

    async def get(self, request: FlashcardRepositoryGetRequest) -> dict | None:
        raise NotImplementedError

    async def create(self, request: FlashcardRepositoryCreateRequest) -> dict:
        raise NotImplementedError

    async def update(self, request: FlashcardRepositoryUpdateRequest) -> dict | None:
        raise NotImplementedError

    async def delete(self, request: FlashcardRepositoryDeleteRequest) -> dict | None:
        raise NotImplementedError
