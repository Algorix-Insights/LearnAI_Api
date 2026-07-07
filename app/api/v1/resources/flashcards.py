from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_flashcards_use_case
from app.application.usecases import FlashcardUseCase
from app.domain.schemas import CrudItemResponse, CrudListResponse
from app.domain.schemas.entities import FlashcardCreate, FlashcardUpdate
from app.domain.schemas.resources.flashcards import (
    FlashcardCreateRequest,
    FlashcardDeleteRequest,
    FlashcardListRequest,
    FlashcardPath,
    FlashcardUpdateRequest,
)

router = APIRouter(prefix="/flashcards", tags=["flashcards"])


@router.get("", response_model=CrudListResponse)
async def list_flashcards(
    request: Annotated[FlashcardListRequest, Depends()],
    use_case: Annotated[FlashcardUseCase, Depends(get_flashcards_use_case)],
) -> CrudListResponse:
    return await use_case.list(request)


@router.post("", response_model=CrudItemResponse, status_code=status.HTTP_201_CREATED)
async def create_flashcard(
    payload: FlashcardCreate,
    use_case: Annotated[FlashcardUseCase, Depends(get_flashcards_use_case)],
) -> CrudItemResponse:
    return await use_case.create(FlashcardCreateRequest(payload=payload))


@router.get("/{flashcard_id}", response_model=CrudItemResponse)
async def get_flashcard(
    path: Annotated[FlashcardPath, Depends()],
    use_case: Annotated[FlashcardUseCase, Depends(get_flashcards_use_case)],
) -> CrudItemResponse:
    return await use_case.get(path)


@router.patch("/{flashcard_id}", response_model=CrudItemResponse)
async def update_flashcard(
    path: Annotated[FlashcardPath, Depends()],
    payload: FlashcardUpdate,
    use_case: Annotated[FlashcardUseCase, Depends(get_flashcards_use_case)],
) -> CrudItemResponse:
    return await use_case.update(
        FlashcardUpdateRequest(flashcard_id=path.flashcard_id, payload=payload)
    )


@router.delete("/{flashcard_id}", response_model=CrudItemResponse)
async def delete_flashcard(
    path: Annotated[FlashcardPath, Depends()],
    use_case: Annotated[FlashcardUseCase, Depends(get_flashcards_use_case)],
) -> CrudItemResponse:
    return await use_case.delete(FlashcardDeleteRequest(flashcard_id=path.flashcard_id))
