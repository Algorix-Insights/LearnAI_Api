from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

from app.domain.schemas.resources.users import UserRead


class AuthRegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=320)
    password: str | None = Field(default=None, min_length=8, max_length=256)
    name: str
    last_name: str
    captcha_token: str | None = Field(default=None, min_length=1, max_length=4096)


class AuthLoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=256)
    captcha_token: str | None = Field(default=None, min_length=1, max_length=4096)


class AuthOtpRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=320)
    should_create_user: bool = False
    captcha_token: str | None = Field(default=None, min_length=1, max_length=4096)


class AuthVerifyOtpRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=320)
    token: str = Field(min_length=6, max_length=2048)
    type: Literal["email", "recovery", "invite", "email_change"] = "email"
    captcha_token: str | None = Field(default=None, min_length=1, max_length=4096)


class AuthForgotPasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=320)
    captcha_token: str | None = Field(default=None, min_length=1, max_length=4096)


class AuthUpdatePasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    password: str = Field(min_length=8, max_length=256)


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
