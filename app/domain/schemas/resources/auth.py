from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

from app.domain.schemas.resources.users import UserRead


class AuthRegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str
    password: str | None = Field(default=None, min_length=6)
    name: str
    last_name: str


class AuthLoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str
    password: str


class AuthOtpRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str
    should_create_user: bool = True


class AuthVerifyOtpRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str
    token: str
    type: Literal["magiclink", "signup", "recovery", "email", "invite"] = "magiclink"


class AuthForgotPasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str
    redirect_to: str | None = None


class AuthUpdatePasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    password: str = Field(min_length=6)


class AuthTokenRead(BaseModel):
    model_config = ConfigDict(extra="allow")

    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_in: int | None = None
    user: UserRead | None = None
    message: str | None = None


class AuthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data: AuthTokenRead


class AuthMessageRead(BaseModel):
    model_config = ConfigDict(extra="allow")

    message: str


class AuthMessageResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data: AuthMessageRead
