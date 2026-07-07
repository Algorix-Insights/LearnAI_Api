from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.schemas.entities import AttemptCreate, AttemptUpdate


class AttemptSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


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
