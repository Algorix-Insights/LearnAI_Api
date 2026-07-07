from app.core.exceptions import EmptyPayloadError, ResourceNotFoundError
from app.domain.interfaces import QuestionRepository
from app.domain.schemas.crud import CrudItemResponse, CrudListResponse
from app.domain.schemas.resources.questions import (
    QuestionCreateRequest,
    QuestionDeleteRequest,
    QuestionListRequest,
    QuestionPath,
    QuestionRepositoryCreateRequest,
    QuestionRepositoryDeleteRequest,
    QuestionRepositoryGetRequest,
    QuestionRepositoryListRequest,
    QuestionRepositoryUpdateRequest,
    QuestionUpdateRequest,
)


class QuestionUseCase:
    def __init__(self, repository: QuestionRepository) -> None:
        self.repository = repository

    async def list(self, request: QuestionListRequest) -> CrudListResponse:
        data = await self.repository.list(
            QuestionRepositoryListRequest(limit=request.limit, offset=request.offset)
        )
        return CrudListResponse(data=data, limit=request.limit, offset=request.offset)

    async def get(self, request: QuestionPath) -> CrudItemResponse:
        data = await self.repository.get(
            QuestionRepositoryGetRequest(question_id=request.question_id)
        )
        if data is None:
            raise ResourceNotFoundError()
        return CrudItemResponse(data=data)

    async def create(self, request: QuestionCreateRequest) -> CrudItemResponse:
        data = await self.repository.create(QuestionRepositoryCreateRequest(payload=request.payload))
        return CrudItemResponse(data=data)

    async def update(self, request: QuestionUpdateRequest) -> CrudItemResponse:
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
        return CrudItemResponse(data=data)

    async def delete(self, request: QuestionDeleteRequest) -> CrudItemResponse:
        data = await self.repository.delete(
            QuestionRepositoryDeleteRequest(question_id=request.question_id)
        )
        if data is None:
            raise ResourceNotFoundError()
        return CrudItemResponse(data=data)
