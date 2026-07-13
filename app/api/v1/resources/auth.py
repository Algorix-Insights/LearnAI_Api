from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPAuthorizationCredentials

from app.api.auth_rate_limit import (
    limit_forgot_password,
    limit_login,
    limit_register,
    limit_reset_password,
    limit_send_otp,
    limit_verify_otp,
)
from app.api.dependencies import bearer_scheme, get_auth_use_case, get_current_user
from app.application.usecases.auth import AuthUseCase
from app.core.exceptions import UnauthorizedError
from app.domain.schemas.resources.auth import (
    AuthForgotPasswordRequest,
    AuthLoginRequest,
    AuthMessageResponse,
    AuthOtpRequest,
    AuthRegisterRequest,
    AuthResponse,
    AuthUpdatePasswordRequest,
    AuthVerifyOtpRequest,
)
from app.domain.schemas.resources.users import UserRead, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(limit_register)],
)
async def register(
    payload: AuthRegisterRequest,
    use_case: Annotated[AuthUseCase, Depends(get_auth_use_case)],
) -> AuthResponse:
    return await use_case.register(payload)


@router.post("/login", response_model=AuthResponse, dependencies=[Depends(limit_login)])
async def login(
    payload: AuthLoginRequest,
    use_case: Annotated[AuthUseCase, Depends(get_auth_use_case)],
) -> AuthResponse:
    return await use_case.login_with_password(payload)


@router.post(
    "/otp",
    response_model=AuthMessageResponse,
    dependencies=[Depends(limit_send_otp)],
)
async def send_otp(
    payload: AuthOtpRequest,
    use_case: Annotated[AuthUseCase, Depends(get_auth_use_case)],
) -> AuthMessageResponse:
    return await use_case.send_otp(payload)


@router.post(
    "/verify-otp",
    response_model=AuthResponse,
    dependencies=[Depends(limit_verify_otp)],
)
async def verify_otp(
    payload: AuthVerifyOtpRequest,
    use_case: Annotated[AuthUseCase, Depends(get_auth_use_case)],
) -> AuthResponse:
    return await use_case.verify_otp(payload)


@router.post(
    "/forgot-password",
    response_model=AuthMessageResponse,
    dependencies=[Depends(limit_forgot_password)],
)
async def forgot_password(
    payload: AuthForgotPasswordRequest,
    use_case: Annotated[AuthUseCase, Depends(get_auth_use_case)],
) -> AuthMessageResponse:
    return await use_case.forgot_password(payload)


@router.post(
    "/reset-password",
    response_model=AuthMessageResponse,
    dependencies=[Depends(limit_reset_password)],
)
async def reset_password(
    payload: AuthUpdatePasswordRequest,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    use_case: Annotated[AuthUseCase, Depends(get_auth_use_case)],
) -> AuthMessageResponse:
    if not credentials or not credentials.credentials:
        raise UnauthorizedError("Se requiere un token de sesión o de recuperación válido en el header Authorization.")
    return await use_case.reset_password(credentials.credentials, payload)


@router.post("/logout", response_model=AuthMessageResponse)
async def logout(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    use_case: Annotated[AuthUseCase, Depends(get_auth_use_case)],
) -> AuthMessageResponse:
    if not credentials or not credentials.credentials:
        raise UnauthorizedError("No autorizado para cerrar sesión. Falta el header Authorization.")
    return await use_case.logout(credentials.credentials)


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: Annotated[UserRead, Depends(get_current_user)],
) -> UserResponse:
    return UserResponse(data=current_user)
