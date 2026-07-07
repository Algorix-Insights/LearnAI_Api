from app.core.exceptions import EmptyPayloadError, ResourceNotFoundError
from app.domain.interfaces import FlashcardRepository
from app.domain.schemas.crud import CrudItemResponse, CrudListResponse
from app.domain.schemas.resources.flashcards import (
    FlashcardCreateRequest,
    FlashcardDeleteRequest,
    FlashcardListRequest,
    FlashcardPath,
    FlashcardRepositoryCreateRequest,
    FlashcardRepositoryDeleteRequest,
    FlashcardRepositoryGetRequest,
    FlashcardRepositoryListRequest,
    FlashcardRepositoryUpdateRequest,
    FlashcardUpdateRequest,
)


class FlashcardUseCase:
    def __init__(self, repository: FlashcardRepository) -> None:
        self.repository = repository

    async def list(self, request: FlashcardListRequest) -> CrudListResponse:
        data = await self.repository.list(
            FlashcardRepositoryListRequest(limit=request.limit, offset=request.offset)
        )
        return CrudListResponse(data=data, limit=request.limit, offset=request.offset)

    async def get(self, request: FlashcardPath) -> CrudItemResponse:
        data = await self.repository.get(
            FlashcardRepositoryGetRequest(flashcard_id=request.flashcard_id)
        )
        if data is None:
            raise ResourceNotFoundError()
        return CrudItemResponse(data=data)

    async def create(self, request: FlashcardCreateRequest) -> CrudItemResponse:
        data = await self.repository.create(
            FlashcardRepositoryCreateRequest(payload=request.payload)
        )
        return CrudItemResponse(data=data)

    async def update(self, request: FlashcardUpdateRequest) -> CrudItemResponse:
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
        return CrudItemResponse(data=data)

    async def delete(self, request: FlashcardDeleteRequest) -> CrudItemResponse:
        data = await self.repository.delete(
            FlashcardRepositoryDeleteRequest(flashcard_id=request.flashcard_id)
        )
        if data is None:
            raise ResourceNotFoundError()
        return CrudItemResponse(data=data)
