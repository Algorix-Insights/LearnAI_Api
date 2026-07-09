from typing import Protocol

from app.domain.schemas.resources.auth import (
    AuthForgotPasswordRequest,
    AuthLoginRequest,
    AuthOtpRequest,
    AuthRegisterRequest,
    AuthUpdatePasswordRequest,
    AuthVerifyOtpRequest,
)


class AuthRepository(Protocol):
    async def sign_up(self, request: AuthRegisterRequest) -> dict:
        raise NotImplementedError

    async def sign_in_with_password(self, request: AuthLoginRequest) -> dict:
        raise NotImplementedError

    async def sign_in_with_otp(self, request: AuthOtpRequest) -> dict:
        raise NotImplementedError

    async def verify_otp(self, request: AuthVerifyOtpRequest) -> dict:
        raise NotImplementedError

    async def reset_password_for_email(self, request: AuthForgotPasswordRequest) -> dict:
        raise NotImplementedError

    async def update_user_password(self, jwt_token: str, request: AuthUpdatePasswordRequest) -> dict:
        raise NotImplementedError

    async def get_user(self, jwt_token: str) -> dict | None:
        raise NotImplementedError

    async def sign_out(self, jwt_token: str) -> None:
        raise NotImplementedError
