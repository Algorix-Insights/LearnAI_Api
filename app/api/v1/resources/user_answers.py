from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_user_answers_use_case
from app.application.usecases import UserAnswerUseCase
from app.domain.schemas.entities import UserAnswerCreate, UserAnswerUpdate
from app.domain.schemas.resources.user_answers import (
    UserAnswerCreateRequest,
    UserAnswerDeleteRequest,
    UserAnswerListResponse,
    UserAnswerListRequest,
    UserAnswerPath,
    UserAnswerResponse,
    UserAnswerUpdateRequest,
)

router = APIRouter(prefix="/user-answers", tags=["user-answers"])


@router.get("", response_model=UserAnswerListResponse)
async def list_user_answers(
    request: Annotated[UserAnswerListRequest, Depends()],
    use_case: Annotated[UserAnswerUseCase, Depends(get_user_answers_use_case)],
) -> UserAnswerListResponse:
    return await use_case.list(request)


@router.post("", response_model=UserAnswerResponse, status_code=status.HTTP_201_CREATED)
async def create_user_answer(
    payload: UserAnswerCreate,
    use_case: Annotated[UserAnswerUseCase, Depends(get_user_answers_use_case)],
) -> UserAnswerResponse:
    return await use_case.create(UserAnswerCreateRequest(payload=payload))


@router.get("/{answer_id}", response_model=UserAnswerResponse)
async def get_user_answer(
    path: Annotated[UserAnswerPath, Depends()],
    use_case: Annotated[UserAnswerUseCase, Depends(get_user_answers_use_case)],
) -> UserAnswerResponse:
    return await use_case.get(path)


@router.patch("/{answer_id}", response_model=UserAnswerResponse)
async def update_user_answer(
    path: Annotated[UserAnswerPath, Depends()],
    payload: UserAnswerUpdate,
    use_case: Annotated[UserAnswerUseCase, Depends(get_user_answers_use_case)],
) -> UserAnswerResponse:
    return await use_case.update(
        UserAnswerUpdateRequest(answer_id=path.answer_id, payload=payload)
    )


@router.delete("/{answer_id}", response_model=UserAnswerResponse)
async def delete_user_answer(
    path: Annotated[UserAnswerPath, Depends()],
    use_case: Annotated[UserAnswerUseCase, Depends(get_user_answers_use_case)],
) -> UserAnswerResponse:
    return await use_case.delete(UserAnswerDeleteRequest(answer_id=path.answer_id))
