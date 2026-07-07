from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_flashcards_use_case
from app.application.usecases import FlashcardUseCase
from app.domain.schemas import (
    CreateItemRequest,
    CrudItemResponse,
    CrudListResponse,
    DeleteItemRequest,
    FlashcardPath,
    ListItemsRequest,
    UpdateItemRequest,
)
from app.domain.schemas.entities import FlashcardCreate, FlashcardUpdate

router = APIRouter(prefix="/flashcards", tags=["flashcards"])


@router.get("", response_model=CrudListResponse)
async def list_flashcards(
    request: Annotated[ListItemsRequest, Depends()],
    use_case: Annotated[FlashcardUseCase, Depends(get_flashcards_use_case)],
) -> CrudListResponse:
    return await use_case.list(request)


@router.post("", response_model=CrudItemResponse, status_code=status.HTTP_201_CREATED)
async def create_flashcard(
    payload: FlashcardCreate,
    use_case: Annotated[FlashcardUseCase, Depends(get_flashcards_use_case)],
) -> CrudItemResponse:
    return await use_case.create(CreateItemRequest(payload=payload))


@router.get("/{flashcard_id}", response_model=CrudItemResponse)
async def get_flashcard(
    path: Annotated[FlashcardPath, Depends()],
    use_case: Annotated[FlashcardUseCase, Depends(get_flashcards_use_case)],
) -> CrudItemResponse:
    return await use_case.get(path.to_item_request())


@router.patch("/{flashcard_id}", response_model=CrudItemResponse)
async def update_flashcard(
    path: Annotated[FlashcardPath, Depends()],
    payload: FlashcardUpdate,
    use_case: Annotated[FlashcardUseCase, Depends(get_flashcards_use_case)],
) -> CrudItemResponse:
    return await use_case.update(
        UpdateItemRequest(item_id=str(path.flashcard_id), payload=payload)
    )


@router.delete("/{flashcard_id}", response_model=CrudItemResponse)
async def delete_flashcard(
    path: Annotated[FlashcardPath, Depends()],
    use_case: Annotated[FlashcardUseCase, Depends(get_flashcards_use_case)],
) -> CrudItemResponse:
    return await use_case.delete(DeleteItemRequest(item_id=str(path.flashcard_id)))
