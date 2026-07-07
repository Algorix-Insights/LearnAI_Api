from app.core.exceptions import EmptyPayloadError, ResourceNotFoundError
from app.domain.interfaces import QuestionOptionRepository
from app.domain.schemas.crud import CrudItemResponse, CrudListResponse
from app.domain.schemas.resources.question_options import (
    QuestionOptionCreateRequest,
    QuestionOptionDeleteRequest,
    QuestionOptionListRequest,
    QuestionOptionPath,
    QuestionOptionRepositoryCreateRequest,
    QuestionOptionRepositoryDeleteRequest,
    QuestionOptionRepositoryGetRequest,
    QuestionOptionRepositoryListRequest,
    QuestionOptionRepositoryUpdateRequest,
    QuestionOptionUpdateRequest,
)


class QuestionOptionUseCase:
    def __init__(self, repository: QuestionOptionRepository) -> None:
        self.repository = repository

    async def list(self, request: QuestionOptionListRequest) -> CrudListResponse:
        data = await self.repository.list(
            QuestionOptionRepositoryListRequest(limit=request.limit, offset=request.offset)
        )
        return CrudListResponse(data=data, limit=request.limit, offset=request.offset)

    async def get(self, request: QuestionOptionPath) -> CrudItemResponse:
        data = await self.repository.get(
            QuestionOptionRepositoryGetRequest(option_id=request.option_id)
        )
        if data is None:
            raise ResourceNotFoundError()
        return CrudItemResponse(data=data)

    async def create(self, request: QuestionOptionCreateRequest) -> CrudItemResponse:
        data = await self.repository.create(
            QuestionOptionRepositoryCreateRequest(payload=request.payload)
        )
        return CrudItemResponse(data=data)

    async def update(self, request: QuestionOptionUpdateRequest) -> CrudItemResponse:
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
        return CrudItemResponse(data=data)

    async def delete(self, request: QuestionOptionDeleteRequest) -> CrudItemResponse:
        data = await self.repository.delete(
            QuestionOptionRepositoryDeleteRequest(option_id=request.option_id)
        )
        if data is None:
            raise ResourceNotFoundError()
        return CrudItemResponse(data=data)
