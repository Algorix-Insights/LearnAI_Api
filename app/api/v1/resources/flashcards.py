from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_flashcards_use_case
from app.application.usecases import FlashcardUseCase
from app.domain.schemas.resources.flashcards import (
    FlashcardDeleteRequest,
    FlashcardListResponse,
    FlashcardListRequest,
    FlashcardPath,
    FlashcardResponse,
)

router = APIRouter(prefix="/flashcards", tags=["flashcards"])


@router.get("", response_model=FlashcardListResponse)
async def list_flashcards(
    request: Annotated[FlashcardListRequest, Depends()],
    use_case: Annotated[FlashcardUseCase, Depends(get_flashcards_use_case)],
) -> FlashcardListResponse:
    return await use_case.list(request)


@router.get("/{flashcard_id}", response_model=FlashcardResponse)
async def get_flashcard(
    path: Annotated[FlashcardPath, Depends()],
    use_case: Annotated[FlashcardUseCase, Depends(get_flashcards_use_case)],
) -> FlashcardResponse:
    return await use_case.get(path)


@router.delete("/{flashcard_id}", response_model=FlashcardResponse)
async def delete_flashcard(
    path: Annotated[FlashcardPath, Depends()],
    use_case: Annotated[FlashcardUseCase, Depends(get_flashcards_use_case)],
) -> FlashcardResponse:
    return await use_case.delete(FlashcardDeleteRequest(flashcard_id=path.flashcard_id))
