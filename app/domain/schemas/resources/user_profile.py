from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserProfileSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class UserSelfUpdate(UserProfileSchema):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)


class ProfilePhotoRead(UserProfileSchema):
    user_id: UUID
    storage_path: str
    mime_type: str
    size_bytes: int
    url: str
    expires_in: int


class ProfilePhotoResponse(UserProfileSchema):
    data: ProfilePhotoRead


class ProfilePhotoDeleteResponse(UserProfileSchema):
    deleted: bool
