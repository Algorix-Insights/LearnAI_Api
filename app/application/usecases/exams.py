from datetime import UTC, datetime

from app.core.exceptions import ResourceNotFoundError
from app.domain.interfaces import ExamRepository
from app.domain.services import ExamService
from app.domain.schemas.resources.exams import (
    ExamCreateRequest,
    ExamDeleteRequest,
    ExamListResponse,
    ExamListRequest,
    ExamPath,
    ExamRepositoryCreateRequest,
    ExamRepositoryDeleteRequest,
    ExamRepositoryGetRequest,
    ExamRepositoryListRequest,
    ExamRepositoryUpdateRequest,
    ExamResponse,
    ExamUpdateRequest,
)


class ExamUseCase:
    def __init__(self, repository: ExamRepository, service: ExamService | None = None) -> None:
        self.repository = repository
        self.service = service or ExamService()

    async def list(self, request: ExamListRequest) -> ExamListResponse:
        data = await self.repository.list(
            ExamRepositoryListRequest(limit=request.limit, offset=request.offset)
        )
        return ExamListResponse(data=data, limit=request.limit, offset=request.offset)

    async def get(self, request: ExamPath) -> ExamResponse:
        data = await self.repository.get(ExamRepositoryGetRequest(exam_id=request.exam_id))
        if data is None:
            raise ResourceNotFoundError()
        return ExamResponse(data=data)

    async def create(self, request: ExamCreateRequest) -> ExamResponse:
        request = self.service.prepare_create(request)
        data = await self.repository.create(ExamRepositoryCreateRequest(payload=request.payload))
        return ExamResponse(data=data)

    async def update(self, request: ExamUpdateRequest) -> ExamResponse:
        request = self.service.prepare_update(request)
        data = await self.repository.update(
            ExamRepositoryUpdateRequest(
                exam_id=request.exam_id,
                payload=request.payload,
                updated_at=datetime.now(UTC),
            )
        )
        if data is None:
            raise ResourceNotFoundError()
        return ExamResponse(data=data)

    async def delete(self, request: ExamDeleteRequest) -> ExamResponse:
        data = await self.repository.delete(ExamRepositoryDeleteRequest(exam_id=request.exam_id))
        if data is None:
            raise ResourceNotFoundError()
        return ExamResponse(data=data)
