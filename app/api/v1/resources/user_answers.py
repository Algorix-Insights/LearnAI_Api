from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_user_answers_use_case
from app.application.usecases import UserAnswerUseCase
from app.domain.schemas import (
    CreateItemRequest,
    CrudItemResponse,
    CrudListResponse,
    DeleteItemRequest,
    ListItemsRequest,
    UpdateItemRequest,
    UserAnswerPath,
)
from app.domain.schemas.entities import UserAnswerCreate, UserAnswerUpdate

router = APIRouter(prefix="/user-answers", tags=["user-answers"])


@router.get("", response_model=CrudListResponse)
async def list_user_answers(
    request: Annotated[ListItemsRequest, Depends()],
    use_case: Annotated[UserAnswerUseCase, Depends(get_user_answers_use_case)],
) -> CrudListResponse:
    return await use_case.list(request)


@router.post("", response_model=CrudItemResponse, status_code=status.HTTP_201_CREATED)
async def create_user_answer(
    payload: UserAnswerCreate,
    use_case: Annotated[UserAnswerUseCase, Depends(get_user_answers_use_case)],
) -> CrudItemResponse:
    return await use_case.create(CreateItemRequest(payload=payload))


@router.get("/{answer_id}", response_model=CrudItemResponse)
async def get_user_answer(
    path: Annotated[UserAnswerPath, Depends()],
    use_case: Annotated[UserAnswerUseCase, Depends(get_user_answers_use_case)],
) -> CrudItemResponse:
    return await use_case.get(path.to_item_request())


@router.patch("/{answer_id}", response_model=CrudItemResponse)
async def update_user_answer(
    path: Annotated[UserAnswerPath, Depends()],
    payload: UserAnswerUpdate,
    use_case: Annotated[UserAnswerUseCase, Depends(get_user_answers_use_case)],
) -> CrudItemResponse:
    return await use_case.update(UpdateItemRequest(item_id=str(path.answer_id), payload=payload))


@router.delete("/{answer_id}", response_model=CrudItemResponse)
async def delete_user_answer(
    path: Annotated[UserAnswerPath, Depends()],
    use_case: Annotated[UserAnswerUseCase, Depends(get_user_answers_use_case)],
) -> CrudItemResponse:
    return await use_case.delete(DeleteItemRequest(item_id=str(path.answer_id)))
