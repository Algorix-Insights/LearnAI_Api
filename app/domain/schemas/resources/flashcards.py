from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.schemas.entities import FlashcardCreate, FlashcardUpdate


class FlashcardSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class FlashcardRead(BaseModel):
    model_config = ConfigDict(extra="allow")

    flashcard_id: UUID | None = None
    notebook_id: UUID | None = None
    question_id: UUID | None = None
    spent_time: int | None = None
    created_at: str | None = None


class FlashcardResponse(FlashcardSchema):
    data: FlashcardRead


class FlashcardListResponse(FlashcardSchema):
    data: list[FlashcardRead]
    limit: int
    offset: int


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
