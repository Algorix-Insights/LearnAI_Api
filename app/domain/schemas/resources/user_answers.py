from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.schemas.entities import UserAnswerCreate, UserAnswerUpdate


class UserAnswerSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class UserAnswerRead(BaseModel):
    model_config = ConfigDict(extra="ignore")

    answer_id: UUID | None = None
    attempt_id: UUID | None = None
    question_id: UUID | None = None
    selected_option_id: UUID | None = None
    answer_text: str | None = None
    created_at: str | None = None


class UserAnswerResponse(UserAnswerSchema):
    data: UserAnswerRead


class UserAnswerListResponse(UserAnswerSchema):
    data: list[UserAnswerRead]
    limit: int
    offset: int


class UserAnswerListRequest(UserAnswerSchema):
    limit: int = Field(default=100, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class UserAnswerPath(UserAnswerSchema):
    answer_id: UUID


class UserAnswerCreateRequest(UserAnswerSchema):
    payload: UserAnswerCreate


class UserAnswerUpdateRequest(UserAnswerSchema):
    answer_id: UUID
    payload: UserAnswerUpdate


class UserAnswerDeleteRequest(UserAnswerSchema):
    answer_id: UUID


class UserAnswerRepositoryListRequest(UserAnswerListRequest):
    pass


class UserAnswerRepositoryGetRequest(UserAnswerPath):
    pass


class UserAnswerRepositoryCreateRequest(UserAnswerCreateRequest):
    pass


class UserAnswerRepositoryUpdateRequest(UserAnswerUpdateRequest):
    pass


class UserAnswerRepositoryDeleteRequest(UserAnswerDeleteRequest):
    pass
