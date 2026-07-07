from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_attempts_use_case
from app.application.usecases import AttemptUseCase
from app.domain.schemas import (
    AttemptPath,
    CreateItemRequest,
    CrudItemResponse,
    CrudListResponse,
    DeleteItemRequest,
    ListItemsRequest,
    UpdateItemRequest,
)
from app.domain.schemas.entities import AttemptCreate, AttemptUpdate

router = APIRouter(prefix="/attempts", tags=["attempts"])


@router.get("", response_model=CrudListResponse)
async def list_attempts(
    request: Annotated[ListItemsRequest, Depends()],
    use_case: Annotated[AttemptUseCase, Depends(get_attempts_use_case)],
) -> CrudListResponse:
    return await use_case.list(request)


@router.post("", response_model=CrudItemResponse, status_code=status.HTTP_201_CREATED)
async def create_attempt(
    payload: AttemptCreate,
    use_case: Annotated[AttemptUseCase, Depends(get_attempts_use_case)],
) -> CrudItemResponse:
    return await use_case.create(CreateItemRequest(payload=payload))


@router.get("/{attempt_id}", response_model=CrudItemResponse)
async def get_attempt(
    path: Annotated[AttemptPath, Depends()],
    use_case: Annotated[AttemptUseCase, Depends(get_attempts_use_case)],
) -> CrudItemResponse:
    return await use_case.get(path.to_item_request())


@router.patch("/{attempt_id}", response_model=CrudItemResponse)
async def update_attempt(
    path: Annotated[AttemptPath, Depends()],
    payload: AttemptUpdate,
    use_case: Annotated[AttemptUseCase, Depends(get_attempts_use_case)],
) -> CrudItemResponse:
    return await use_case.update(
        UpdateItemRequest(item_id=str(path.attempt_id), payload=payload)
    )


@router.delete("/{attempt_id}", response_model=CrudItemResponse)
async def delete_attempt(
    path: Annotated[AttemptPath, Depends()],
    use_case: Annotated[AttemptUseCase, Depends(get_attempts_use_case)],
) -> CrudItemResponse:
    return await use_case.delete(DeleteItemRequest(item_id=str(path.attempt_id)))
