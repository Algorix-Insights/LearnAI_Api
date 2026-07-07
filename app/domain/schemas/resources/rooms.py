from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.schemas.entities import RoomCreate, RoomUpdate


class RoomSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RoomRead(BaseModel):
    model_config = ConfigDict(extra="allow")

    room_id: UUID | None = None
    name: str | None = None
    description: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class RoomResponse(RoomSchema):
    data: RoomRead


class RoomListResponse(RoomSchema):
    data: list[RoomRead]
    limit: int
    offset: int


class RoomListRequest(RoomSchema):
    limit: int = Field(default=100, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class RoomPath(RoomSchema):
    room_id: UUID


class RoomCreateRequest(RoomSchema):
    payload: RoomCreate


class RoomUpdateRequest(RoomSchema):
    room_id: UUID
    payload: RoomUpdate


class RoomDeleteRequest(RoomSchema):
    room_id: UUID


class RoomRepositoryListRequest(RoomListRequest):
    pass


class RoomRepositoryGetRequest(RoomPath):
    pass


class RoomRepositoryCreateRequest(RoomCreateRequest):
    pass


class RoomRepositoryUpdateRequest(RoomUpdateRequest):
    updated_at: datetime


class RoomRepositoryDeleteRequest(RoomDeleteRequest):
    pass


class AddRoomMemberRequest(RoomSchema):
    member_id: UUID
    role: str = Field(default="member", pattern="^(member|admin)$")


class RoomMemberPath(RoomSchema):
    room_id: UUID
    member_id: UUID


class RoomMemberRepositoryCreateRequest(RoomSchema):
    room_id: UUID
    member_id: UUID
    role: str = Field(default="member", pattern="^(member|admin)$")


class RoomMemberRepositoryDeleteRequest(RoomMemberPath):
    pass


class RoomMemberRead(BaseModel):
    model_config = ConfigDict(extra="allow")

    room_id: UUID | None = None
    member_id: UUID | None = None
    role: str | None = None
    joined_at: datetime | None = None


class RoomMemberResponse(RoomSchema):
    data: RoomMemberRead


class AddRoomNotebookRequest(RoomSchema):
    notebook_id: UUID
    created_by: UUID


class RoomNotebookPath(RoomSchema):
    room_id: UUID
    notebook_id: UUID


class RoomNotebookRepositoryCreateRequest(RoomSchema):
    room_id: UUID
    notebook_id: UUID
    created_by: UUID


class RoomNotebookRepositoryDeleteRequest(RoomNotebookPath):
    pass


class RoomNotebookRead(BaseModel):
    model_config = ConfigDict(extra="allow")

    room_id: UUID | None = None
    notebook_id: UUID | None = None
    created_by: UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class RoomNotebookResponse(RoomSchema):
    data: RoomNotebookRead
