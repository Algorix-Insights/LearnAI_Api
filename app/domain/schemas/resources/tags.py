from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.schemas.entities import TagCreate, TagUpdate


class TagSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TagRead(TagSchema):
    id: UUID
    name: str
    status: Literal["active", "inactive"]
    scope: Literal["system", "user"]


class TagResponse(TagSchema):
    data: TagRead


class TagListResponse(TagSchema):
    data: list[TagRead]
    limit: int
    offset: int


class TagListRequest(TagSchema):
    limit: int = Field(default=100, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class TagPath(TagSchema):
    tag_id: UUID


class TagCreateRequest(TagSchema):
    payload: TagCreate


class TagUpdateRequest(TagSchema):
    tag_id: UUID
    payload: TagUpdate


class TagDeleteRequest(TagSchema):
    tag_id: UUID


class TagRepositoryListRequest(TagListRequest):
    user_id: UUID


class TagRepositoryGetRequest(TagPath):
    user_id: UUID


class TagRepositoryCreateRequest(TagCreateRequest):
    user_id: UUID


class TagRepositoryUpdateRequest(TagUpdateRequest):
    user_id: UUID


class TagRepositoryDeleteRequest(TagDeleteRequest):
    user_id: UUID
