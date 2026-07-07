from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.schemas.entities import UserAnswerCreate, UserAnswerUpdate


class UserAnswerSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


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
