from app.core.exceptions import ResourceNotFoundError
from app.domain.interfaces import ExamQuestionRepository
from app.domain.services import ExamService
from app.domain.schemas.resources.exams import (
    AddExamQuestionRequest,
    ExamQuestionPath,
    ExamQuestionRepositoryCreateRequest,
    ExamQuestionRepositoryDeleteRequest,
    ExamQuestionResponse,
)


class ExamQuestionUseCase:
    def __init__(
        self, repository: ExamQuestionRepository, service: ExamService | None = None
    ) -> None:
        self.repository = repository
        self.service = service or ExamService()

    async def add(self, exam_id: str, request: AddExamQuestionRequest) -> ExamQuestionResponse:
        request = self.service.prepare_question(request)
        data = await self.repository.create(
            ExamQuestionRepositoryCreateRequest(
                exam_id=exam_id,
                question_id=request.question_id,
                question_order=request.question_order,
                points=request.points,
            )
        )
        return ExamQuestionResponse(data=data)

    async def remove(self, request: ExamQuestionPath) -> ExamQuestionResponse:
        data = await self.repository.delete(
            ExamQuestionRepositoryDeleteRequest(
                exam_id=request.exam_id,
                question_id=request.question_id,
            )
        )
        if data is None:
            raise ResourceNotFoundError()
        return ExamQuestionResponse(data=data)
