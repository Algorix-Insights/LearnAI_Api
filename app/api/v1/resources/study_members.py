from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_study_members_use_case
from app.application.usecases import StudyMemberUseCase
from app.domain.schemas import (
    CreateItemRequest,
    CrudItemResponse,
    CrudListResponse,
    DeleteItemRequest,
    ListItemsRequest,
    StudyMemberPath,
    UpdateItemRequest,
)
from app.domain.schemas.entities import StudyMemberCreate, StudyMemberUpdate

router = APIRouter(prefix="/study-members", tags=["study-members"])


@router.get("", response_model=CrudListResponse)
async def list_study_members(
    request: Annotated[ListItemsRequest, Depends()],
    use_case: Annotated[StudyMemberUseCase, Depends(get_study_members_use_case)],
) -> CrudListResponse:
    return await use_case.list(request)


@router.post("", response_model=CrudItemResponse, status_code=status.HTTP_201_CREATED)
async def create_study_member(
    payload: StudyMemberCreate,
    use_case: Annotated[StudyMemberUseCase, Depends(get_study_members_use_case)],
) -> CrudItemResponse:
    return await use_case.create(CreateItemRequest(payload=payload))


@router.get("/{member_id}", response_model=CrudItemResponse)
async def get_study_member(
    path: Annotated[StudyMemberPath, Depends()],
    use_case: Annotated[StudyMemberUseCase, Depends(get_study_members_use_case)],
) -> CrudItemResponse:
    return await use_case.get(path.to_item_request())


@router.patch("/{member_id}", response_model=CrudItemResponse)
async def update_study_member(
    path: Annotated[StudyMemberPath, Depends()],
    payload: StudyMemberUpdate,
    use_case: Annotated[StudyMemberUseCase, Depends(get_study_members_use_case)],
) -> CrudItemResponse:
    return await use_case.update(UpdateItemRequest(item_id=str(path.member_id), payload=payload))


@router.delete("/{member_id}", response_model=CrudItemResponse)
async def delete_study_member(
    path: Annotated[StudyMemberPath, Depends()],
    use_case: Annotated[StudyMemberUseCase, Depends(get_study_members_use_case)],
) -> CrudItemResponse:
    return await use_case.delete(DeleteItemRequest(item_id=str(path.member_id)))
