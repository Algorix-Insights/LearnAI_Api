from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.schemas.entities import UserCreate, UserUpdate


class UserSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class UserRead(BaseModel):
    model_config = ConfigDict(extra="allow")

    user_id: UUID | None = None
    name: str | None = None
    last_name: str | None = None
    email: str | None = None
    streak: int | None = None
    status: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    last_login: datetime | None = None


class UserResponse(UserSchema):
    data: UserRead


class UserListResponse(UserSchema):
    data: list[UserRead]
    limit: int
    offset: int


class UserListRequest(UserSchema):
    limit: int = Field(default=100, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class UserPath(UserSchema):
    user_id: UUID


class UserCreateRequest(UserSchema):
    payload: UserCreate


class UserUpdateRequest(UserSchema):
    user_id: UUID
    payload: UserUpdate


class UserDeleteRequest(UserSchema):
    user_id: UUID


class UserRepositoryListRequest(UserListRequest):
    pass


class UserRepositoryGetRequest(UserPath):
    pass


class UserRepositoryCreateRequest(UserCreateRequest):
    pass


class UserRepositoryUpdateRequest(UserUpdateRequest):
    updated_at: datetime


class UserRepositoryDeleteRequest(UserDeleteRequest):
    pass


class PersonalNotebookPath(UserSchema):
    user_id: UUID
    notebook_id: UUID


class PersonalNotebookRepositoryCreateRequest(PersonalNotebookPath):
    pass


class PersonalNotebookRepositoryDeleteRequest(PersonalNotebookPath):
    pass


class PersonalNotebookRead(BaseModel):
    model_config = ConfigDict(extra="allow")

    user_id: UUID | None = None
    notebook_id: UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PersonalNotebookResponse(UserSchema):
    data: PersonalNotebookRead
