from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.schemas.entities import FlashcardCreate, FlashcardUpdate


class FlashcardSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class FlashcardListRequest(FlashcardSchema):
    limit: int = Field(default=100, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class FlashcardPath(FlashcardSchema):
    flashcard_id: UUID


class FlashcardCreateRequest(FlashcardSchema):
    payload: FlashcardCreate


class FlashcardUpdateRequest(FlashcardSchema):
    flashcard_id: UUID
    payload: FlashcardUpdate


class FlashcardDeleteRequest(FlashcardSchema):
    flashcard_id: UUID


class FlashcardRepositoryListRequest(FlashcardListRequest):
    pass


class FlashcardRepositoryGetRequest(FlashcardPath):
    pass


class FlashcardRepositoryCreateRequest(FlashcardCreateRequest):
    pass


class FlashcardRepositoryUpdateRequest(FlashcardUpdateRequest):
    pass


class FlashcardRepositoryDeleteRequest(FlashcardDeleteRequest):
    pass
