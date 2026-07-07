from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.schemas.entities import QuestionOptionCreate, QuestionOptionUpdate


class QuestionOptionSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class QuestionOptionRead(BaseModel):
    model_config = ConfigDict(extra="allow")

    option_id: UUID | None = None
    question_id: UUID | None = None
    option_text: str | None = None
    is_correct: bool | None = None
    option_order: int | None = None
    created_at: str | None = None


class QuestionOptionResponse(QuestionOptionSchema):
    data: QuestionOptionRead


class QuestionOptionListResponse(QuestionOptionSchema):
    data: list[QuestionOptionRead]
    limit: int
    offset: int


class QuestionOptionListRequest(QuestionOptionSchema):
    limit: int = Field(default=100, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class QuestionOptionPath(QuestionOptionSchema):
    option_id: UUID


class QuestionOptionCreateRequest(QuestionOptionSchema):
    payload: QuestionOptionCreate


class QuestionOptionUpdateRequest(QuestionOptionSchema):
    option_id: UUID
    payload: QuestionOptionUpdate


class QuestionOptionDeleteRequest(QuestionOptionSchema):
    option_id: UUID


class QuestionOptionRepositoryListRequest(QuestionOptionListRequest):
    pass


class QuestionOptionRepositoryGetRequest(QuestionOptionPath):
    pass


class QuestionOptionRepositoryCreateRequest(QuestionOptionCreateRequest):
    pass


class QuestionOptionRepositoryUpdateRequest(QuestionOptionUpdateRequest):
    pass


class QuestionOptionRepositoryDeleteRequest(QuestionOptionDeleteRequest):
    pass
