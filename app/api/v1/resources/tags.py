from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_tags_use_case
from app.application.usecases import TagUseCase
from app.domain.schemas.entities import TagCreate, TagUpdate
from app.domain.schemas.resources.tags import (
    TagCreateRequest,
    TagDeleteRequest,
    TagListResponse,
    TagListRequest,
    TagPath,
    TagResponse,
    TagUpdateRequest,
)

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=TagListResponse)
async def list_tags(
    request: Annotated[TagListRequest, Depends()],
    use_case: Annotated[TagUseCase, Depends(get_tags_use_case)],
) -> TagListResponse:
    return await use_case.list(request)


@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    payload: TagCreate,
    use_case: Annotated[TagUseCase, Depends(get_tags_use_case)],
) -> TagResponse:
    return await use_case.create(TagCreateRequest(payload=payload))


@router.get("/{tag_id}", response_model=TagResponse)
async def get_tag(
    path: Annotated[TagPath, Depends()],
    use_case: Annotated[TagUseCase, Depends(get_tags_use_case)],
) -> TagResponse:
    return await use_case.get(path)


@router.patch("/{tag_id}", response_model=TagResponse)
async def update_tag(
    path: Annotated[TagPath, Depends()],
    payload: TagUpdate,
    use_case: Annotated[TagUseCase, Depends(get_tags_use_case)],
) -> TagResponse:
    return await use_case.update(TagUpdateRequest(tag_id=path.tag_id, payload=payload))


@router.delete("/{tag_id}", response_model=TagResponse)
async def delete_tag(
    path: Annotated[TagPath, Depends()],
    use_case: Annotated[TagUseCase, Depends(get_tags_use_case)],
) -> TagResponse:
    return await use_case.delete(TagDeleteRequest(tag_id=path.tag_id))
