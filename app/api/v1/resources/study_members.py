from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_study_members_use_case
from app.application.usecases import StudyMemberUseCase
from app.domain.schemas import CrudItemResponse, CrudListResponse
from app.domain.schemas.entities import StudyMemberCreate, StudyMemberUpdate
from app.domain.schemas.resources.study_members import (
    StudyMemberCreateRequest,
    StudyMemberDeleteRequest,
    StudyMemberListRequest,
    StudyMemberPath,
    StudyMemberUpdateRequest,
)

router = APIRouter(prefix="/study-members", tags=["study-members"])


@router.get("", response_model=CrudListResponse)
async def list_study_members(
    request: Annotated[StudyMemberListRequest, Depends()],
    use_case: Annotated[StudyMemberUseCase, Depends(get_study_members_use_case)],
) -> CrudListResponse:
    return await use_case.list(request)


@router.post("", response_model=CrudItemResponse, status_code=status.HTTP_201_CREATED)
async def create_study_member(
    payload: StudyMemberCreate,
    use_case: Annotated[StudyMemberUseCase, Depends(get_study_members_use_case)],
) -> CrudItemResponse:
    return await use_case.create(StudyMemberCreateRequest(payload=payload))


@router.get("/{member_id}", response_model=CrudItemResponse)
async def get_study_member(
    path: Annotated[StudyMemberPath, Depends()],
    use_case: Annotated[StudyMemberUseCase, Depends(get_study_members_use_case)],
) -> CrudItemResponse:
    return await use_case.get(path)


@router.patch("/{member_id}", response_model=CrudItemResponse)
async def update_study_member(
    path: Annotated[StudyMemberPath, Depends()],
    payload: StudyMemberUpdate,
    use_case: Annotated[StudyMemberUseCase, Depends(get_study_members_use_case)],
) -> CrudItemResponse:
    return await use_case.update(StudyMemberUpdateRequest(member_id=path.member_id, payload=payload))


@router.delete("/{member_id}", response_model=CrudItemResponse)
async def delete_study_member(
    path: Annotated[StudyMemberPath, Depends()],
    use_case: Annotated[StudyMemberUseCase, Depends(get_study_members_use_case)],
) -> CrudItemResponse:
    return await use_case.delete(StudyMemberDeleteRequest(member_id=path.member_id))
