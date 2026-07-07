from app.core.exceptions import EmptyPayloadError, ResourceNotFoundError
from app.domain.interfaces import FlashcardRepository
from app.domain.schemas.resources.flashcards import (
    FlashcardCreateRequest,
    FlashcardDeleteRequest,
    FlashcardListResponse,
    FlashcardListRequest,
    FlashcardPath,
    FlashcardRepositoryCreateRequest,
    FlashcardRepositoryDeleteRequest,
    FlashcardRepositoryGetRequest,
    FlashcardRepositoryListRequest,
    FlashcardRepositoryUpdateRequest,
    FlashcardResponse,
    FlashcardUpdateRequest,
)


class FlashcardUseCase:
    def __init__(self, repository: FlashcardRepository) -> None:
        self.repository = repository

    async def list(self, request: FlashcardListRequest) -> FlashcardListResponse:
        data = await self.repository.list(
            FlashcardRepositoryListRequest(limit=request.limit, offset=request.offset)
        )
        return FlashcardListResponse(data=data, limit=request.limit, offset=request.offset)

    async def get(self, request: FlashcardPath) -> FlashcardResponse:
        data = await self.repository.get(
            FlashcardRepositoryGetRequest(flashcard_id=request.flashcard_id)
        )
        if data is None:
            raise ResourceNotFoundError()
        return FlashcardResponse(data=data)

    async def create(self, request: FlashcardCreateRequest) -> FlashcardResponse:
        data = await self.repository.create(
            FlashcardRepositoryCreateRequest(payload=request.payload)
        )
        return FlashcardResponse(data=data)

    async def update(self, request: FlashcardUpdateRequest) -> FlashcardResponse:
        if not request.payload.model_dump(exclude_unset=True):
            raise EmptyPayloadError()
        data = await self.repository.update(
            FlashcardRepositoryUpdateRequest(
                flashcard_id=request.flashcard_id,
                payload=request.payload,
            )
        )
        if data is None:
            raise ResourceNotFoundError()
        return FlashcardResponse(data=data)

    async def delete(self, request: FlashcardDeleteRequest) -> FlashcardResponse:
        data = await self.repository.delete(
            FlashcardRepositoryDeleteRequest(flashcard_id=request.flashcard_id)
        )
        if data is None:
            raise ResourceNotFoundError()
        return FlashcardResponse(data=data)
