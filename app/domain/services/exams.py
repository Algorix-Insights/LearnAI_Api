from app.core.exceptions import EmptyPayloadError
from app.domain.schemas.resources.exams import (
    AddExamQuestionRequest,
    ExamCreateRequest,
    ExamUpdateRequest,
)


class ExamService:
    def prepare_create(self, request: ExamCreateRequest) -> ExamCreateRequest:
        payload = request.payload.model_copy(update={"name": request.payload.name.strip()})
        return ExamCreateRequest(payload=payload)

    def prepare_update(self, request: ExamUpdateRequest) -> ExamUpdateRequest:
        if not request.payload.model_dump(exclude_unset=True):
            raise EmptyPayloadError()
        if request.payload.name is None:
            return request
        payload = request.payload.model_copy(update={"name": request.payload.name.strip()})
        return ExamUpdateRequest(exam_id=request.exam_id, payload=payload)

    def prepare_question(self, request: AddExamQuestionRequest) -> AddExamQuestionRequest:
        return request
