from typing import Any

from supabase import Client
from supabase_auth.helpers import parse_user_response

from app.core.exceptions import AuthError, InvalidCredentialsError, RepositoryError, UnauthorizedError
from app.domain.interfaces.auth import AuthRepository
from app.domain.schemas.resources.auth import (
    AuthForgotPasswordRequest,
    AuthLoginRequest,
    AuthOtpRequest,
    AuthRegisterRequest,
    AuthUpdatePasswordRequest,
    AuthVerifyOtpRequest,
)
from app.infra.db.supabase import get_supabase_client


class SupabaseAuthRepository(AuthRepository):
    def __init__(self, client: Client | None = None) -> None:
        self.client = client or get_supabase_client()

    async def sign_up(self, request: AuthRegisterRequest) -> dict:
        try:
            if not request.password:
                self.client.auth.sign_in_with_otp(
                    {
                        "email": request.email,
                        "options": {
                            "should_create_user": True,
                            "data": {
                                "name": request.name,
                                "last_name": request.last_name,
                            },
                        },
                    }
                )
                return {
                    "access_token": "",
                    "refresh_token": None,
                    "token_type": "bearer",
                    "expires_in": None,
                    "user": {
                        "id": "",
                        "email": request.email,
                        "user_metadata": {
                            "name": request.name,
                            "last_name": request.last_name,
                        },
                    },
                    "message": "Registro iniciado. Revisa tu correo para verificar y entrar con el Magic Link o código OTP.",
                }

            response = self.client.auth.sign_up(
                {
                    "email": request.email,
                    "password": request.password,
                    "options": {
                        "data": {
                            "name": request.name,
                            "last_name": request.last_name,
                        }
                    },
                }
            )
            return self._format_auth_response(response)
        except Exception as exc:
            msg = str(exc)
            if "already registered" in msg.lower() or "unique" in msg.lower():
                raise AuthError("El correo electrónico ya está registrado.") from exc
            raise AuthError(f"Error en registro: {msg}") from exc

    async def sign_in_with_password(self, request: AuthLoginRequest) -> dict:
        try:
            response = self.client.auth.sign_in_with_password(
                {
                    "email": request.email,
                    "password": request.password,
                }
            )
            return self._format_auth_response(response)
        except Exception as exc:
            msg = str(exc)
            if "invalid login credentials" in msg.lower() or "invalid" in msg.lower() or "incorrect" in msg.lower():
                raise InvalidCredentialsError() from exc
            raise AuthError(f"Error al iniciar sesión: {msg}") from exc

    async def sign_in_with_otp(self, request: AuthOtpRequest) -> dict:
        try:
            self.client.auth.sign_in_with_otp(
                {
                    "email": request.email,
                    "options": {
                        "should_create_user": request.should_create_user,
                    },
                }
            )
            return {"message": "Código OTP / enlace enviado al correo exitosamente."}
        except Exception as exc:
            raise AuthError(f"Error al enviar OTP: {str(exc)}") from exc

    async def verify_otp(self, request: AuthVerifyOtpRequest) -> dict:
        try:
            response = self.client.auth.verify_otp(
                {
                    "email": request.email,
                    "token": request.token,
                    "type": request.type,
                }
            )
            return self._format_auth_response(response)
        except Exception as exc:
            raise UnauthorizedError(f"Código o token inválido o expirado: {str(exc)}") from exc

    async def reset_password_for_email(self, request: AuthForgotPasswordRequest) -> dict:
        try:
            options = {}
            if request.redirect_to:
                options["redirect_to"] = request.redirect_to
            self.client.auth.reset_password_for_email(request.email, options=options or None)
            return {"message": "Enlace de recuperación enviado al correo exitosamente."}
        except Exception as exc:
            raise AuthError(f"Error al solicitar recuperación de contraseña: {str(exc)}") from exc

    async def update_user_password(self, jwt_token: str, request: AuthUpdatePasswordRequest) -> dict:
        try:
            # Llamamos a _request del cliente auth pasando el jwt especificado del usuario
            response = self.client.auth._request(
                "PUT",
                "user",
                body={"password": request.password},
                jwt=jwt_token,
            )
            # Extraemos o verificamos el usuario con parse_user_response importado arriba
            user_response = parse_user_response(response)
            if not user_response.user:
                raise AuthError("No se pudo actualizar la contraseña.")
            return {
                "id": str(user_response.user.id),
                "email": user_response.user.email,
                "user_metadata": user_response.user.user_metadata or {},
            }
        except Exception as exc:
            raise AuthError(f"Error al actualizar la contraseña: {str(exc)}") from exc

    async def get_user(self, jwt_token: str) -> dict | None:
        try:
            user_response = self.client.auth.get_user(jwt_token)
            if not user_response or not user_response.user:
                return None
            user = user_response.user
            return {
                "id": str(user.id),
                "email": user.email,
                "user_metadata": user.user_metadata or {},
            }
        except Exception:
            return None

    async def sign_out(self, jwt_token: str) -> None:
        try:
            self.client.auth._request(
                "POST",
                "logout",
                jwt=jwt_token,
            )
        except Exception:
            # Ignoramos si el token ya expiró o la sesión fue cerrada
            pass

    def _format_auth_response(self, response: Any) -> dict:
        if isinstance(response, dict):
            return response

        user = getattr(response, "user", None)
        session = getattr(response, "session", None)

        if not user:
            raise AuthError("No se recibió información de usuario de Supabase Auth.")

        user_data = {
            "id": str(user.id),
            "email": user.email,
            "user_metadata": user.user_metadata or {},
        }

        if session:
            return {
                "access_token": session.access_token,
                "refresh_token": session.refresh_token,
                "token_type": getattr(session, "token_type", "bearer") or "bearer",
                "expires_in": getattr(session, "expires_in", None),
                "user": user_data,
            }
        else:
            return {
                "access_token": "",
                "refresh_token": None,
                "token_type": "bearer",
                "expires_in": None,
                "user": user_data,
            }
