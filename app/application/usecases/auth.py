from uuid import UUID

from app.core.exceptions import AuthError, UnauthorizedError
from app.domain.interfaces.auth import AuthRepository
from app.domain.interfaces.users import UserRepository
from app.domain.schemas.entities import UserCreate
from app.domain.schemas.resources.auth import (
    AuthForgotPasswordRequest,
    AuthLoginRequest,
    AuthMessageRead,
    AuthMessageResponse,
    AuthOtpRequest,
    AuthRegisterRequest,
    AuthResponse,
    AuthTokenRead,
    AuthUpdatePasswordRequest,
    AuthVerifyOtpRequest,
)
from app.domain.schemas.resources.users import UserRepositoryCreateRequest, UserRepositoryGetRequest, UserRead


class AuthUseCase:
    def __init__(self, auth_repository: AuthRepository, user_repository: UserRepository) -> None:
        self.auth_repository = auth_repository
        self.user_repository = user_repository

    async def register(self, request: AuthRegisterRequest) -> AuthResponse:
        res = await self.auth_repository.sign_up(request)
        return await self._build_auth_response(res)

    async def login_with_password(self, request: AuthLoginRequest) -> AuthResponse:
        res = await self.auth_repository.sign_in_with_password(request)
        return await self._build_auth_response(res)

    async def send_otp(self, request: AuthOtpRequest) -> AuthMessageResponse:
        res = await self.auth_repository.sign_in_with_otp(request)
        return AuthMessageResponse(data=AuthMessageRead(message=res.get("message", "Código OTP enviado exitosamente.")))

    async def verify_otp(self, request: AuthVerifyOtpRequest) -> AuthResponse:
        res = await self.auth_repository.verify_otp(request)
        return await self._build_auth_response(res)

    async def forgot_password(self, request: AuthForgotPasswordRequest) -> AuthMessageResponse:
        res = await self.auth_repository.reset_password_for_email(request)
        return AuthMessageResponse(data=AuthMessageRead(message=res.get("message", "Enlace de recuperación enviado.")))

    async def reset_password(self, jwt_token: str, request: AuthUpdatePasswordRequest) -> AuthMessageResponse:
        await self.auth_repository.update_user_password(jwt_token, request)
        return AuthMessageResponse(data=AuthMessageRead(message="Contraseña actualizada exitosamente."))

    async def get_current_user_profile(self, jwt_token: str) -> UserRead:
        if not jwt_token:
            raise UnauthorizedError("Token de autenticación faltante.")
        user_dict = await self.auth_repository.get_user(jwt_token)
        if not user_dict:
            raise UnauthorizedError("Sesión inválida o expirada.")
        return await self._sync_user_profile(user_dict)

    async def logout(self, jwt_token: str) -> AuthMessageResponse:
        await self.auth_repository.sign_out(jwt_token)
        return AuthMessageResponse(data=AuthMessageRead(message="Sesión cerrada exitosamente."))

    async def _build_auth_response(self, response_dict: dict) -> AuthResponse:
        user_dict = response_dict.get("user")
        if not user_dict:
            raise AuthError("Información de usuario faltante en la respuesta de autenticación.")

        user_id_str = user_dict.get("id")
        if not user_id_str:
            metadata = user_dict.get("user_metadata", {})
            user_read = UserRead(
                user_id="00000000-0000-0000-0000-000000000000",
                name=metadata.get("name", "Usuario"),
                last_name=metadata.get("last_name", "Supabase"),
                email=user_dict.get("email", ""),
                status="pending",
            )
        else:
            user_read = await self._sync_user_profile(user_dict)

        token_read = AuthTokenRead(
            access_token=response_dict.get("access_token", ""),
            refresh_token=response_dict.get("refresh_token"),
            token_type=response_dict.get("token_type", "bearer") or "bearer",
            expires_in=response_dict.get("expires_in"),
            user=user_read,
            message=response_dict.get("message"),
        )
        return AuthResponse(data=token_read)

    async def _sync_user_profile(self, user_dict: dict) -> UserRead:
        user_id_str = user_dict.get("id")
        if not user_id_str:
            raise AuthError("ID de usuario no válido al sincronizar perfil.")
        user_id = UUID(user_id_str)

        try:
            existing = await self.user_repository.get(UserRepositoryGetRequest(user_id=user_id))
            if existing is not None:
                return self._to_user_read(existing)
        except Exception:
            pass

        metadata = user_dict.get("user_metadata", {})
        name = metadata.get("name", "Usuario")
        last_name = metadata.get("last_name", "Supabase")
        email = user_dict.get("email", "")

        payload = UserCreate(
            user_id=user_id,
            name=name,
            last_name=last_name,
            email=email,
            hash_password=None,
            streak=0,
            status="active",
        )
        try:
            created = await self.user_repository.create(UserRepositoryCreateRequest(payload=payload))
            return self._to_user_read(created)
        except Exception:
            return UserRead(
                user_id=user_id,
                name=name,
                last_name=last_name,
                email=email,
                status="active",
            )

    def _to_user_read(self, item: dict) -> UserRead:
        safe_dict = {key: value for key, value in item.items() if key != "hash_password"}
        return UserRead.model_validate(safe_dict)
