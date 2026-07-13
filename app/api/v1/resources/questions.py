from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_questions_use_case
from app.application.usecases import QuestionUseCase
from app.domain.schemas.entities import QuestionUpdate
from app.domain.schemas.resources.questions import (
    QuestionDeleteRequest,
    QuestionListResponse,
    QuestionListRequest,
    QuestionPath,
    QuestionResponse,
    QuestionUpdateRequest,
)

router = APIRouter(prefix="/questions", tags=["questions"])


@router.get("", response_model=QuestionListResponse)
async def list_questions(
    request: Annotated[QuestionListRequest, Depends()],
    use_case: Annotated[QuestionUseCase, Depends(get_questions_use_case)],
) -> QuestionListResponse:
    return await use_case.list(request)


@router.get("/{question_id}", response_model=QuestionResponse)
async def get_question(
    path: Annotated[QuestionPath, Depends()],
    use_case: Annotated[QuestionUseCase, Depends(get_questions_use_case)],
) -> QuestionResponse:
    return await use_case.get(path)


@router.patch("/{question_id}", response_model=QuestionResponse)
async def update_question(
    path: Annotated[QuestionPath, Depends()],
    payload: QuestionUpdate,
    use_case: Annotated[QuestionUseCase, Depends(get_questions_use_case)],
) -> QuestionResponse:
    return await use_case.update(
        QuestionUpdateRequest(question_id=path.question_id, payload=payload)
    )


@router.delete("/{question_id}", response_model=QuestionResponse)
async def delete_question(
    path: Annotated[QuestionPath, Depends()],
    use_case: Annotated[QuestionUseCase, Depends(get_questions_use_case)],
) -> QuestionResponse:
    return await use_case.delete(QuestionDeleteRequest(question_id=path.question_id))
