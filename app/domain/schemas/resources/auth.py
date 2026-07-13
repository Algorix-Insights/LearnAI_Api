from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.domain.schemas.resources.users import UserRead


class AuthRegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=320)
    password: str | None = Field(default=None, min_length=8, max_length=256)
    name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    captcha_token: str | None = Field(default=None, min_length=1, max_length=4096)


class AuthLoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=256)
    captcha_token: str | None = Field(default=None, min_length=1, max_length=4096)


class AuthOtpRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=320)
    # Account creation belongs to /auth/register, which also captures profile data.
    should_create_user: Literal[False] = False
    captcha_token: str | None = Field(default=None, min_length=1, max_length=4096)


class AuthVerifyOtpRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str | None = Field(default=None, min_length=3, max_length=320)
    token: str | None = Field(default=None, min_length=6, max_length=2048)
    token_hash: str | None = Field(default=None, min_length=6, max_length=4096)
    type: Literal["email", "recovery", "invite", "email_change"] = "email"
    captcha_token: str | None = Field(default=None, min_length=1, max_length=4096)

    @field_validator("email", "token", "token_hash", mode="before")
    @classmethod
    def strip_verification_values(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def validate_verification_challenge(self) -> "AuthVerifyOtpRequest":
        if (self.token is None) == (self.token_hash is None):
            raise ValueError("Debe enviar exactamente uno de token o token_hash.")
        if self.token is not None and self.email is None:
            raise ValueError("El email es obligatorio al verificar un código OTP.")
        return self


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
