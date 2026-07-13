from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_tags_use_case
from app.application.usecases import TagUseCase
from app.domain.schemas.resources.tags import (
    TagListResponse,
    TagListRequest,
    TagPath,
    TagResponse,
)

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=TagListResponse)
async def list_tags(
    request: Annotated[TagListRequest, Depends()],
    use_case: Annotated[TagUseCase, Depends(get_tags_use_case)],
) -> TagListResponse:
    return await use_case.list(request)


@router.get("/{tag_id}", response_model=TagResponse)
async def get_tag(
    path: Annotated[TagPath, Depends()],
    use_case: Annotated[TagUseCase, Depends(get_tags_use_case)],
) -> TagResponse:
    return await use_case.get(path)
