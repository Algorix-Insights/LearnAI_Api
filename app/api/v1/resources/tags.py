from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_current_user, get_tags_use_case
from app.application.usecases import TagUseCase
from app.core.exceptions import UnauthorizedError
from app.domain.schemas.entities import TagCreate
from app.domain.schemas.resources.tags import (
    TagCreateRequest,
    TagListResponse,
    TagListRequest,
    TagPath,
    TagResponse,
)
from app.domain.schemas.resources.users import UserRead

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=TagListResponse)
async def list_tags(
    request: Annotated[TagListRequest, Depends()],
    current_user: Annotated[UserRead, Depends(get_current_user)],
    use_case: Annotated[TagUseCase, Depends(get_tags_use_case)],
) -> TagListResponse:
    return await use_case.list(request, user_id=_actor_id(current_user))


@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    payload: TagCreate,
    current_user: Annotated[UserRead, Depends(get_current_user)],
    use_case: Annotated[TagUseCase, Depends(get_tags_use_case)],
) -> TagResponse:
    return await use_case.create(
        TagCreateRequest(payload=payload),
        user_id=_actor_id(current_user),
    )


@router.get("/{tag_id}", response_model=TagResponse)
async def get_tag(
    path: Annotated[TagPath, Depends()],
    current_user: Annotated[UserRead, Depends(get_current_user)],
    use_case: Annotated[TagUseCase, Depends(get_tags_use_case)],
) -> TagResponse:
    return await use_case.get(path, user_id=_actor_id(current_user))


def _actor_id(current_user: UserRead) -> UUID:
    if current_user.user_id is None:
        raise UnauthorizedError()
    return current_user.user_id
