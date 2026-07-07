from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.schemas.entities import StudyMemberCreate, StudyMemberUpdate


class StudyMemberSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class StudyMemberListRequest(StudyMemberSchema):
    limit: int = Field(default=100, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class StudyMemberPath(StudyMemberSchema):
    member_id: UUID


class StudyMemberCreateRequest(StudyMemberSchema):
    payload: StudyMemberCreate


class StudyMemberUpdateRequest(StudyMemberSchema):
    member_id: UUID
    payload: StudyMemberUpdate


class StudyMemberDeleteRequest(StudyMemberSchema):
    member_id: UUID


class StudyMemberRepositoryListRequest(StudyMemberListRequest):
    pass


class StudyMemberRepositoryGetRequest(StudyMemberPath):
    pass


class StudyMemberRepositoryCreateRequest(StudyMemberCreateRequest):
    pass


class StudyMemberRepositoryUpdateRequest(StudyMemberUpdateRequest):
    updated_at: datetime


class StudyMemberRepositoryDeleteRequest(StudyMemberDeleteRequest):
    pass
