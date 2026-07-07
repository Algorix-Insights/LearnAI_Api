from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.schemas.entities import NotebookCreate, NotebookUpdate


class NotebookSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class NotebookRead(BaseModel):
    model_config = ConfigDict(extra="allow")

    notebook_id: UUID | None = None
    name: str | None = None
    description: str | None = None
    grade: int | None = None
    summary: str | None = None
    is_dominated: bool | None = None
    is_favorite: bool | None = None
    status: str | None = None
    spent_time: int | None = None
    last_seen_at: datetime | None = None
    due_date: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class NotebookResponse(NotebookSchema):
    data: NotebookRead


class NotebookListResponse(NotebookSchema):
    data: list[NotebookRead]
    limit: int
    offset: int


class NotebookListRequest(NotebookSchema):
    limit: int = Field(default=100, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class NotebookPath(NotebookSchema):
    notebook_id: UUID


class NotebookCreateRequest(NotebookSchema):
    payload: NotebookCreate


class NotebookUpdateRequest(NotebookSchema):
    notebook_id: UUID
    payload: NotebookUpdate


class NotebookDeleteRequest(NotebookSchema):
    notebook_id: UUID


class NotebookRepositoryListRequest(NotebookListRequest):
    pass


class NotebookRepositoryGetRequest(NotebookPath):
    pass


class NotebookRepositoryCreateRequest(NotebookCreateRequest):
    pass


class NotebookRepositoryUpdateRequest(NotebookUpdateRequest):
    updated_at: datetime


class NotebookRepositoryDeleteRequest(NotebookDeleteRequest):
    pass


class NotebookTagPath(NotebookSchema):
    notebook_id: UUID
    tag_id: UUID


class NotebookTagRepositoryCreateRequest(NotebookTagPath):
    pass


class NotebookTagRepositoryDeleteRequest(NotebookTagPath):
    pass


class NotebookTagRead(BaseModel):
    model_config = ConfigDict(extra="allow")

    notebook_id: UUID | None = None
    tag_id: UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class NotebookTagResponse(NotebookSchema):
    data: NotebookTagRead
