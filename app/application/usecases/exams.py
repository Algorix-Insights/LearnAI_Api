from datetime import UTC, datetime

from app.core.exceptions import EmptyPayloadError, ResourceNotFoundError
from app.domain.interfaces import ExamRepository
from app.domain.schemas.crud import CrudItemResponse, CrudListResponse
from app.domain.schemas.resources.exams import (
    ExamCreateRequest,
    ExamDeleteRequest,
    ExamListRequest,
    ExamPath,
    ExamRepositoryCreateRequest,
    ExamRepositoryDeleteRequest,
    ExamRepositoryGetRequest,
    ExamRepositoryListRequest,
    ExamRepositoryUpdateRequest,
    ExamUpdateRequest,
)


class ExamUseCase:
    def __init__(self, repository: ExamRepository) -> None:
        self.repository = repository

    async def list(self, request: ExamListRequest) -> CrudListResponse:
        data = await self.repository.list(
            ExamRepositoryListRequest(limit=request.limit, offset=request.offset)
        )
        return CrudListResponse(data=data, limit=request.limit, offset=request.offset)

    async def get(self, request: ExamPath) -> CrudItemResponse:
        data = await self.repository.get(ExamRepositoryGetRequest(exam_id=request.exam_id))
        if data is None:
            raise ResourceNotFoundError()
        return CrudItemResponse(data=data)

    async def create(self, request: ExamCreateRequest) -> CrudItemResponse:
        data = await self.repository.create(ExamRepositoryCreateRequest(payload=request.payload))
        return CrudItemResponse(data=data)

    async def update(self, request: ExamUpdateRequest) -> CrudItemResponse:
        if not request.payload.model_dump(exclude_unset=True):
            raise EmptyPayloadError()
        data = await self.repository.update(
            ExamRepositoryUpdateRequest(
                exam_id=request.exam_id,
                payload=request.payload,
                updated_at=datetime.now(UTC),
            )
        )
        if data is None:
            raise ResourceNotFoundError()
        return CrudItemResponse(data=data)

    async def delete(self, request: ExamDeleteRequest) -> CrudItemResponse:
        data = await self.repository.delete(ExamRepositoryDeleteRequest(exam_id=request.exam_id))
        if data is None:
            raise ResourceNotFoundError()
        return CrudItemResponse(data=data)
