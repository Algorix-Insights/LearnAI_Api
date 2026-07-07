from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_question_options_use_case
from app.application.usecases import QuestionOptionUseCase
from app.domain.schemas import (
    CreateItemRequest,
    CrudItemResponse,
    CrudListResponse,
    DeleteItemRequest,
    ListItemsRequest,
    QuestionOptionPath,
    UpdateItemRequest,
)
from app.domain.schemas.entities import QuestionOptionCreate, QuestionOptionUpdate

router = APIRouter(prefix="/question-options", tags=["question-options"])


@router.get("", response_model=CrudListResponse)
async def list_question_options(
    request: Annotated[ListItemsRequest, Depends()],
    use_case: Annotated[QuestionOptionUseCase, Depends(get_question_options_use_case)],
) -> CrudListResponse:
    return await use_case.list(request)


@router.post("", response_model=CrudItemResponse, status_code=status.HTTP_201_CREATED)
async def create_question_option(
    payload: QuestionOptionCreate,
    use_case: Annotated[QuestionOptionUseCase, Depends(get_question_options_use_case)],
) -> CrudItemResponse:
    return await use_case.create(CreateItemRequest(payload=payload))


@router.get("/{option_id}", response_model=CrudItemResponse)
async def get_question_option(
    path: Annotated[QuestionOptionPath, Depends()],
    use_case: Annotated[QuestionOptionUseCase, Depends(get_question_options_use_case)],
) -> CrudItemResponse:
    return await use_case.get(path.to_item_request())


@router.patch("/{option_id}", response_model=CrudItemResponse)
async def update_question_option(
    path: Annotated[QuestionOptionPath, Depends()],
    payload: QuestionOptionUpdate,
    use_case: Annotated[QuestionOptionUseCase, Depends(get_question_options_use_case)],
) -> CrudItemResponse:
    return await use_case.update(UpdateItemRequest(item_id=str(path.option_id), payload=payload))


@router.delete("/{option_id}", response_model=CrudItemResponse)
async def delete_question_option(
    path: Annotated[QuestionOptionPath, Depends()],
    use_case: Annotated[QuestionOptionUseCase, Depends(get_question_options_use_case)],
) -> CrudItemResponse:
    return await use_case.delete(DeleteItemRequest(item_id=str(path.option_id)))
