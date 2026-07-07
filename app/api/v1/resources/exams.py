from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_exam_questions_use_case, get_exams_use_case
from app.application.usecases import ExamQuestionUseCase, ExamUseCase
from app.domain.schemas.entities import ExamCreate, ExamUpdate
from app.domain.schemas.resources.exams import (
    AddExamQuestionRequest,
    ExamCreateRequest,
    ExamDeleteRequest,
    ExamListResponse,
    ExamListRequest,
    ExamPath,
    ExamQuestionPath,
    ExamQuestionResponse,
    ExamResponse,
    ExamUpdateRequest,
)

router = APIRouter(prefix="/exams", tags=["exams"])


@router.get("", response_model=ExamListResponse)
async def list_exams(
    request: Annotated[ExamListRequest, Depends()],
    use_case: Annotated[ExamUseCase, Depends(get_exams_use_case)],
) -> ExamListResponse:
    return await use_case.list(request)


@router.post("", response_model=ExamResponse, status_code=status.HTTP_201_CREATED)
async def create_exam(
    payload: ExamCreate,
    use_case: Annotated[ExamUseCase, Depends(get_exams_use_case)],
) -> ExamResponse:
    return await use_case.create(ExamCreateRequest(payload=payload))


@router.get("/{exam_id}", response_model=ExamResponse)
async def get_exam(
    path: Annotated[ExamPath, Depends()],
    use_case: Annotated[ExamUseCase, Depends(get_exams_use_case)],
) -> ExamResponse:
    return await use_case.get(path)


@router.patch("/{exam_id}", response_model=ExamResponse)
async def update_exam(
    path: Annotated[ExamPath, Depends()],
    payload: ExamUpdate,
    use_case: Annotated[ExamUseCase, Depends(get_exams_use_case)],
) -> ExamResponse:
    return await use_case.update(ExamUpdateRequest(exam_id=path.exam_id, payload=payload))


@router.delete("/{exam_id}", response_model=ExamResponse)
async def delete_exam(
    path: Annotated[ExamPath, Depends()],
    use_case: Annotated[ExamUseCase, Depends(get_exams_use_case)],
) -> ExamResponse:
    return await use_case.delete(ExamDeleteRequest(exam_id=path.exam_id))


@router.post(
    "/{exam_id}/questions",
    response_model=ExamQuestionResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["exam-questions"],
)
async def add_question_to_exam(
    path: Annotated[ExamPath, Depends()],
    payload: AddExamQuestionRequest,
    use_case: Annotated[ExamQuestionUseCase, Depends(get_exam_questions_use_case)],
) -> ExamQuestionResponse:
    return await use_case.add(str(path.exam_id), payload)


@router.delete(
    "/{exam_id}/questions/{question_id}",
    response_model=ExamQuestionResponse,
    tags=["exam-questions"],
)
async def remove_question_from_exam(
    path: Annotated[ExamQuestionPath, Depends()],
    use_case: Annotated[ExamQuestionUseCase, Depends(get_exam_questions_use_case)],
) -> ExamQuestionResponse:
    return await use_case.remove(path)
