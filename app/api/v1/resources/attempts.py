from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_attempts_use_case
from app.application.usecases import AttemptUseCase
from app.domain.schemas.entities import AttemptCreate, AttemptUpdate
from app.domain.schemas.resources.attempts import (
    AttemptCreateRequest,
    AttemptDeleteRequest,
    AttemptListResponse,
    AttemptListRequest,
    AttemptPath,
    AttemptResponse,
    AttemptUpdateRequest,
)

router = APIRouter(prefix="/attempts", tags=["attempts"])


@router.get("", response_model=AttemptListResponse)
async def list_attempts(
    request: Annotated[AttemptListRequest, Depends()],
    use_case: Annotated[AttemptUseCase, Depends(get_attempts_use_case)],
) -> AttemptListResponse:
    return await use_case.list(request)


@router.post("", response_model=AttemptResponse, status_code=status.HTTP_201_CREATED)
async def create_attempt(
    payload: AttemptCreate,
    use_case: Annotated[AttemptUseCase, Depends(get_attempts_use_case)],
) -> AttemptResponse:
    return await use_case.create(AttemptCreateRequest(payload=payload))


@router.get("/{attempt_id}", response_model=AttemptResponse)
async def get_attempt(
    path: Annotated[AttemptPath, Depends()],
    use_case: Annotated[AttemptUseCase, Depends(get_attempts_use_case)],
) -> AttemptResponse:
    return await use_case.get(path)


@router.patch("/{attempt_id}", response_model=AttemptResponse)
async def update_attempt(
    path: Annotated[AttemptPath, Depends()],
    payload: AttemptUpdate,
    use_case: Annotated[AttemptUseCase, Depends(get_attempts_use_case)],
) -> AttemptResponse:
    return await use_case.update(AttemptUpdateRequest(attempt_id=path.attempt_id, payload=payload))


@router.delete("/{attempt_id}", response_model=AttemptResponse)
async def delete_attempt(
    path: Annotated[AttemptPath, Depends()],
    use_case: Annotated[AttemptUseCase, Depends(get_attempts_use_case)],
) -> AttemptResponse:
    return await use_case.delete(AttemptDeleteRequest(attempt_id=path.attempt_id))
