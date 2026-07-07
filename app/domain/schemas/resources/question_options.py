from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.schemas.entities import QuestionOptionCreate, QuestionOptionUpdate


class QuestionOptionSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


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
