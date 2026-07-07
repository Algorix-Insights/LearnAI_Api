from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.schemas.entities import TagCreate, TagUpdate


class TagSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TagRead(BaseModel):
    model_config = ConfigDict(extra="allow")

    tag_id: UUID | None = None
    id: UUID | None = None
    name: str | None = None
    status: str | None = None


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
    pass


class TagRepositoryGetRequest(TagPath):
    pass


class TagRepositoryCreateRequest(TagCreateRequest):
    pass


class TagRepositoryUpdateRequest(TagUpdateRequest):
    pass


class TagRepositoryDeleteRequest(TagDeleteRequest):
    pass
