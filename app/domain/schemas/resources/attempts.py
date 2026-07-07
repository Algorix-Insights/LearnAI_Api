from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.schemas.entities import AttemptCreate, AttemptUpdate


class AttemptSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AttemptRead(BaseModel):
    model_config = ConfigDict(extra="allow")

    attempt_id: UUID | None = None
    exam_id: UUID | None = None
    user_id: UUID | None = None
    score: float | None = None
    status: str | None = None
    created_at: str | None = None
    completed_at: str | None = None
    started_at: str | None = None
    spent_time: int | None = None


class AttemptResponse(AttemptSchema):
    data: AttemptRead


class AttemptListResponse(AttemptSchema):
    data: list[AttemptRead]
    limit: int
    offset: int


class AttemptListRequest(AttemptSchema):
    limit: int = Field(default=100, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class AttemptPath(AttemptSchema):
    attempt_id: UUID


class AttemptCreateRequest(AttemptSchema):
    payload: AttemptCreate


class AttemptUpdateRequest(AttemptSchema):
    attempt_id: UUID
    payload: AttemptUpdate


class AttemptDeleteRequest(AttemptSchema):
    attempt_id: UUID


class AttemptRepositoryListRequest(AttemptListRequest):
    pass


class AttemptRepositoryGetRequest(AttemptPath):
    pass


class AttemptRepositoryCreateRequest(AttemptCreateRequest):
    pass


class AttemptRepositoryUpdateRequest(AttemptUpdateRequest):
    pass


class AttemptRepositoryDeleteRequest(AttemptDeleteRequest):
    pass
