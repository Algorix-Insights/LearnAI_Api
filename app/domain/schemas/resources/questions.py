from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.schemas.entities import QuestionCreate, QuestionUpdate


class QuestionSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class QuestionListRequest(QuestionSchema):
    limit: int = Field(default=100, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class QuestionPath(QuestionSchema):
    question_id: UUID


class QuestionCreateRequest(QuestionSchema):
    payload: QuestionCreate


class QuestionUpdateRequest(QuestionSchema):
    question_id: UUID
    payload: QuestionUpdate


class QuestionDeleteRequest(QuestionSchema):
    question_id: UUID


class QuestionRepositoryListRequest(QuestionListRequest):
    pass


class QuestionRepositoryGetRequest(QuestionPath):
    pass


class QuestionRepositoryCreateRequest(QuestionCreateRequest):
    pass


class QuestionRepositoryUpdateRequest(QuestionUpdateRequest):
    pass


class QuestionRepositoryDeleteRequest(QuestionDeleteRequest):
    pass
