from app.core.exceptions import EmptyPayloadError, ResourceNotFoundError
from app.domain.interfaces import UserAnswerRepository
from app.domain.schemas.crud import CrudItemResponse, CrudListResponse
from app.domain.schemas.resources.user_answers import (
    UserAnswerCreateRequest,
    UserAnswerDeleteRequest,
    UserAnswerListRequest,
    UserAnswerPath,
    UserAnswerRepositoryCreateRequest,
    UserAnswerRepositoryDeleteRequest,
    UserAnswerRepositoryGetRequest,
    UserAnswerRepositoryListRequest,
    UserAnswerRepositoryUpdateRequest,
    UserAnswerUpdateRequest,
)


class UserAnswerUseCase:
    def __init__(self, repository: UserAnswerRepository) -> None:
        self.repository = repository

    async def list(self, request: UserAnswerListRequest) -> CrudListResponse:
        data = await self.repository.list(
            UserAnswerRepositoryListRequest(limit=request.limit, offset=request.offset)
        )
        return CrudListResponse(data=data, limit=request.limit, offset=request.offset)

    async def get(self, request: UserAnswerPath) -> CrudItemResponse:
        data = await self.repository.get(UserAnswerRepositoryGetRequest(answer_id=request.answer_id))
        if data is None:
            raise ResourceNotFoundError()
        return CrudItemResponse(data=data)

    async def create(self, request: UserAnswerCreateRequest) -> CrudItemResponse:
        data = await self.repository.create(
            UserAnswerRepositoryCreateRequest(payload=request.payload)
        )
        return CrudItemResponse(data=data)

    async def update(self, request: UserAnswerUpdateRequest) -> CrudItemResponse:
        if not request.payload.model_dump(exclude_unset=True):
            raise EmptyPayloadError()
        data = await self.repository.update(
            UserAnswerRepositoryUpdateRequest(answer_id=request.answer_id, payload=request.payload)
        )
        if data is None:
            raise ResourceNotFoundError()
        return CrudItemResponse(data=data)

    async def delete(self, request: UserAnswerDeleteRequest) -> CrudItemResponse:
        data = await self.repository.delete(
            UserAnswerRepositoryDeleteRequest(answer_id=request.answer_id)
        )
        if data is None:
            raise ResourceNotFoundError()
        return CrudItemResponse(data=data)
