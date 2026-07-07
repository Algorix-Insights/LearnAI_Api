from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_exam_questions_use_case, get_exams_use_case
from app.application.usecases import ExamQuestionUseCase, ExamUseCase
from app.domain.schemas import (
    AddExamQuestionRequest,
    CreateItemRequest,
    CrudItemResponse,
    CrudListResponse,
    DeleteItemRequest,
    ExamPath,
    ExamQuestionPath,
    ListItemsRequest,
    UpdateItemRequest,
)
from app.domain.schemas.entities import ExamCreate, ExamUpdate

router = APIRouter(prefix="/exams", tags=["exams"])


@router.get("", response_model=CrudListResponse)
async def list_exams(
    request: Annotated[ListItemsRequest, Depends()],
    use_case: Annotated[ExamUseCase, Depends(get_exams_use_case)],
) -> CrudListResponse:
    return await use_case.list(request)


@router.post("", response_model=CrudItemResponse, status_code=status.HTTP_201_CREATED)
async def create_exam(
    payload: ExamCreate,
    use_case: Annotated[ExamUseCase, Depends(get_exams_use_case)],
) -> CrudItemResponse:
    return await use_case.create(CreateItemRequest(payload=payload))


@router.get("/{exam_id}", response_model=CrudItemResponse)
async def get_exam(
    path: Annotated[ExamPath, Depends()],
    use_case: Annotated[ExamUseCase, Depends(get_exams_use_case)],
) -> CrudItemResponse:
    return await use_case.get(path.to_item_request())


@router.patch("/{exam_id}", response_model=CrudItemResponse)
async def update_exam(
    path: Annotated[ExamPath, Depends()],
    payload: ExamUpdate,
    use_case: Annotated[ExamUseCase, Depends(get_exams_use_case)],
) -> CrudItemResponse:
    return await use_case.update(UpdateItemRequest(item_id=str(path.exam_id), payload=payload))


@router.delete("/{exam_id}", response_model=CrudItemResponse)
async def delete_exam(
    path: Annotated[ExamPath, Depends()],
    use_case: Annotated[ExamUseCase, Depends(get_exams_use_case)],
) -> CrudItemResponse:
    return await use_case.delete(DeleteItemRequest(item_id=str(path.exam_id)))


@router.post(
    "/{exam_id}/questions",
    response_model=CrudItemResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["exam-questions"],
)
async def add_question_to_exam(
    path: Annotated[ExamPath, Depends()],
    payload: AddExamQuestionRequest,
    use_case: Annotated[ExamQuestionUseCase, Depends(get_exam_questions_use_case)],
) -> CrudItemResponse:
    return await use_case.add(str(path.exam_id), payload)


@router.delete(
    "/{exam_id}/questions/{question_id}",
    response_model=CrudItemResponse,
    tags=["exam-questions"],
)
async def remove_question_from_exam(
    path: Annotated[ExamQuestionPath, Depends()],
    use_case: Annotated[ExamQuestionUseCase, Depends(get_exam_questions_use_case)],
) -> CrudItemResponse:
    return await use_case.remove(path)
