from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.schemas.entities import NotebookCreate, NotebookUpdate


class NotebookSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


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
