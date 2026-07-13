from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_question_options_use_case
from app.application.usecases import QuestionOptionUseCase
from app.domain.schemas.entities import QuestionOptionUpdate
from app.domain.schemas.resources.question_options import (
    QuestionOptionDeleteRequest,
    QuestionOptionListResponse,
    QuestionOptionListRequest,
    QuestionOptionPath,
    QuestionOptionResponse,
    QuestionOptionUpdateRequest,
)

router = APIRouter(prefix="/question-options", tags=["question-options"])


@router.get("", response_model=QuestionOptionListResponse)
async def list_question_options(
    request: Annotated[QuestionOptionListRequest, Depends()],
    use_case: Annotated[QuestionOptionUseCase, Depends(get_question_options_use_case)],
) -> QuestionOptionListResponse:
    return await use_case.list(request)


@router.get("/{option_id}", response_model=QuestionOptionResponse)
async def get_question_option(
    path: Annotated[QuestionOptionPath, Depends()],
    use_case: Annotated[QuestionOptionUseCase, Depends(get_question_options_use_case)],
) -> QuestionOptionResponse:
    return await use_case.get(path)


@router.patch("/{option_id}", response_model=QuestionOptionResponse)
async def update_question_option(
    path: Annotated[QuestionOptionPath, Depends()],
    payload: QuestionOptionUpdate,
    use_case: Annotated[QuestionOptionUseCase, Depends(get_question_options_use_case)],
) -> QuestionOptionResponse:
    return await use_case.update(
        QuestionOptionUpdateRequest(option_id=path.option_id, payload=payload)
    )


@router.delete("/{option_id}", response_model=QuestionOptionResponse)
async def delete_question_option(
    path: Annotated[QuestionOptionPath, Depends()],
    use_case: Annotated[QuestionOptionUseCase, Depends(get_question_options_use_case)],
) -> QuestionOptionResponse:
    return await use_case.delete(QuestionOptionDeleteRequest(option_id=path.option_id))
