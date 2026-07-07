from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.schemas.entities import StudyMemberCreate, StudyMemberUpdate


class StudyMemberSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class StudyMemberRead(BaseModel):
    model_config = ConfigDict(extra="allow")

    member_id: UUID | None = None
    user_id: UUID | None = None
    nickname: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class StudyMemberResponse(StudyMemberSchema):
    data: StudyMemberRead


class StudyMemberListResponse(StudyMemberSchema):
    data: list[StudyMemberRead]
    limit: int
    offset: int


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
