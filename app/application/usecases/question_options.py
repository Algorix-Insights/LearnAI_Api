from app.core.exceptions import EmptyPayloadError, ResourceNotFoundError
from app.domain.interfaces import QuestionOptionRepository
from app.domain.schemas.resources.question_options import (
    QuestionOptionCreateRequest,
    QuestionOptionDeleteRequest,
    QuestionOptionListResponse,
    QuestionOptionListRequest,
    QuestionOptionPath,
    QuestionOptionRepositoryCreateRequest,
    QuestionOptionRepositoryDeleteRequest,
    QuestionOptionRepositoryGetRequest,
    QuestionOptionRepositoryListRequest,
    QuestionOptionRepositoryUpdateRequest,
    QuestionOptionResponse,
    QuestionOptionUpdateRequest,
)


class QuestionOptionUseCase:
    def __init__(self, repository: QuestionOptionRepository) -> None:
        self.repository = repository

    async def list(self, request: QuestionOptionListRequest) -> QuestionOptionListResponse:
        data = await self.repository.list(
            QuestionOptionRepositoryListRequest(limit=request.limit, offset=request.offset)
        )
        return QuestionOptionListResponse(data=data, limit=request.limit, offset=request.offset)

    async def get(self, request: QuestionOptionPath) -> QuestionOptionResponse:
        data = await self.repository.get(
            QuestionOptionRepositoryGetRequest(option_id=request.option_id)
        )
        if data is None:
            raise ResourceNotFoundError()
        return QuestionOptionResponse(data=data)

    async def create(self, request: QuestionOptionCreateRequest) -> QuestionOptionResponse:
        data = await self.repository.create(
            QuestionOptionRepositoryCreateRequest(payload=request.payload)
        )
        return QuestionOptionResponse(data=data)

    async def update(self, request: QuestionOptionUpdateRequest) -> QuestionOptionResponse:
        if not request.payload.model_dump(exclude_unset=True):
            raise EmptyPayloadError()
        data = await self.repository.update(
            QuestionOptionRepositoryUpdateRequest(
                option_id=request.option_id,
                payload=request.payload,
            )
        )
        if data is None:
            raise ResourceNotFoundError()
        return QuestionOptionResponse(data=data)

    async def delete(self, request: QuestionOptionDeleteRequest) -> QuestionOptionResponse:
        data = await self.repository.delete(
            QuestionOptionRepositoryDeleteRequest(option_id=request.option_id)
        )
        if data is None:
            raise ResourceNotFoundError()
        return QuestionOptionResponse(data=data)
