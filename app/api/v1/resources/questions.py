from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_questions_use_case
from app.application.usecases import QuestionUseCase
from app.domain.schemas import CrudItemResponse, CrudListResponse
from app.domain.schemas.entities import QuestionCreate, QuestionUpdate
from app.domain.schemas.resources.questions import (
    QuestionCreateRequest,
    QuestionDeleteRequest,
    QuestionListRequest,
    QuestionPath,
    QuestionUpdateRequest,
)

router = APIRouter(prefix="/questions", tags=["questions"])


@router.get("", response_model=CrudListResponse)
async def list_questions(
    request: Annotated[QuestionListRequest, Depends()],
    use_case: Annotated[QuestionUseCase, Depends(get_questions_use_case)],
) -> CrudListResponse:
    return await use_case.list(request)


@router.post("", response_model=CrudItemResponse, status_code=status.HTTP_201_CREATED)
async def create_question(
    payload: QuestionCreate,
    use_case: Annotated[QuestionUseCase, Depends(get_questions_use_case)],
) -> CrudItemResponse:
    return await use_case.create(QuestionCreateRequest(payload=payload))


@router.get("/{question_id}", response_model=CrudItemResponse)
async def get_question(
    path: Annotated[QuestionPath, Depends()],
    use_case: Annotated[QuestionUseCase, Depends(get_questions_use_case)],
) -> CrudItemResponse:
    return await use_case.get(path)


@router.patch("/{question_id}", response_model=CrudItemResponse)
async def update_question(
    path: Annotated[QuestionPath, Depends()],
    payload: QuestionUpdate,
    use_case: Annotated[QuestionUseCase, Depends(get_questions_use_case)],
) -> CrudItemResponse:
    return await use_case.update(
        QuestionUpdateRequest(question_id=path.question_id, payload=payload)
    )


@router.delete("/{question_id}", response_model=CrudItemResponse)
async def delete_question(
    path: Annotated[QuestionPath, Depends()],
    use_case: Annotated[QuestionUseCase, Depends(get_questions_use_case)],
) -> CrudItemResponse:
    return await use_case.delete(QuestionDeleteRequest(question_id=path.question_id))
