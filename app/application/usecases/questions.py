from app.core.exceptions import EmptyPayloadError, ResourceNotFoundError
from app.domain.interfaces import QuestionRepository
from app.domain.schemas.resources.questions import (
    QuestionCreateRequest,
    QuestionDeleteRequest,
    QuestionListResponse,
    QuestionListRequest,
    QuestionPath,
    QuestionRepositoryCreateRequest,
    QuestionRepositoryDeleteRequest,
    QuestionRepositoryGetRequest,
    QuestionRepositoryListRequest,
    QuestionRepositoryUpdateRequest,
    QuestionResponse,
    QuestionUpdateRequest,
)


class QuestionUseCase:
    def __init__(self, repository: QuestionRepository) -> None:
        self.repository = repository

    async def list(self, request: QuestionListRequest) -> QuestionListResponse:
        data = await self.repository.list(
            QuestionRepositoryListRequest(limit=request.limit, offset=request.offset)
        )
        return QuestionListResponse(data=data, limit=request.limit, offset=request.offset)

    async def get(self, request: QuestionPath) -> QuestionResponse:
        data = await self.repository.get(
            QuestionRepositoryGetRequest(question_id=request.question_id)
        )
        if data is None:
            raise ResourceNotFoundError()
        return QuestionResponse(data=data)

    async def create(self, request: QuestionCreateRequest) -> QuestionResponse:
        data = await self.repository.create(QuestionRepositoryCreateRequest(payload=request.payload))
        return QuestionResponse(data=data)

    async def update(self, request: QuestionUpdateRequest) -> QuestionResponse:
        if not request.payload.model_dump(exclude_unset=True):
            raise EmptyPayloadError()
        data = await self.repository.update(
            QuestionRepositoryUpdateRequest(
                question_id=request.question_id,
                payload=request.payload,
            )
        )
        if data is None:
            raise ResourceNotFoundError()
        return QuestionResponse(data=data)

    async def delete(self, request: QuestionDeleteRequest) -> QuestionResponse:
        data = await self.repository.delete(
            QuestionRepositoryDeleteRequest(question_id=request.question_id)
        )
        if data is None:
            raise ResourceNotFoundError()
        return QuestionResponse(data=data)
