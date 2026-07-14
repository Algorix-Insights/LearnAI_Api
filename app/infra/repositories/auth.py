import asyncio
from typing import Any, NoReturn

from supabase import Client
from supabase_auth.errors import (
    AuthApiError,
    AuthError as SupabaseAuthException,
    AuthRetryableError,
)
from supabase_auth.helpers import parse_user_response

from app.core.config import get_settings
from app.core.exceptions import (
    ApiError,
    AuthError,
    AuthRateLimitError,
    AuthUnavailableError,
    InvalidCredentialsError,
    UnauthorizedError,
)
from app.domain.interfaces.auth import AuthRepository
from app.domain.schemas.resources.auth import (
    AuthForgotPasswordRequest,
    AuthLoginRequest,
    AuthOtpRequest,
    AuthRegisterRequest,
    AuthUpdatePasswordRequest,
    AuthVerifyOtpRequest,
)
from app.infra.db.supabase import get_supabase_auth_client


class SupabaseAuthRepository(AuthRepository):
    def __init__(
        self,
        client: Client | None = None,
        recovery_redirect_url: str | None = None,
    ) -> None:
        self.client = client or get_supabase_auth_client()
        self.recovery_redirect_url = (
            recovery_redirect_url
            if recovery_redirect_url is not None
            else get_settings().auth_recovery_redirect_url
        )

    async def sign_up(self, request: AuthRegisterRequest) -> dict:
        try:
            if not request.password:
                await asyncio.to_thread(
                    self.client.auth.sign_in_with_otp,
                    {
                        "email": request.email,
                        "options": {
                            "should_create_user": True,
                            "captcha_token": request.captcha_token,
                            "data": {
                                "name": request.name,
                                "last_name": request.last_name,
                            },
                        },
                    },
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

            response = await asyncio.to_thread(
                self.client.auth.sign_up,
                {
                    "email": request.email,
                    "password": request.password,
                    "options": {
                        "captcha_token": request.captcha_token,
                        "data": {
                            "name": request.name,
                            "last_name": request.last_name,
                        }
                    },
                },
            )
            return self._format_auth_response(response)
        except ApiError:
            raise
        except SupabaseAuthException as exc:
            self._raise_provider_error(exc, operation="register")
        except Exception as exc:
            raise AuthUnavailableError() from exc

    async def sign_in_with_password(self, request: AuthLoginRequest) -> dict:
        try:
            response = await asyncio.to_thread(
                self.client.auth.sign_in_with_password,
                {
                    "email": request.email,
                    "password": request.password,
                    "options": {
                        "captcha_token": request.captcha_token,
                    },
                },
            )
            return self._format_auth_response(response)
        except ApiError:
            raise
        except SupabaseAuthException as exc:
            self._raise_provider_error(exc, operation="login")
        except Exception as exc:
            raise AuthUnavailableError() from exc

    async def sign_in_with_otp(self, request: AuthOtpRequest) -> dict:
        try:
            await asyncio.to_thread(
                self.client.auth.sign_in_with_otp,
                {
                    "email": request.email,
                    "options": {
                        "should_create_user": request.should_create_user,
                        "captcha_token": request.captcha_token,
                    },
                },
            )
            return {"message": "Código OTP / enlace enviado al correo exitosamente."}
        except ApiError:
            raise
        except SupabaseAuthException as exc:
            self._raise_provider_error(exc, operation="send-otp")
        except Exception as exc:
            raise AuthUnavailableError() from exc

    async def verify_otp(self, request: AuthVerifyOtpRequest) -> dict:
        try:
            payload: dict[str, Any] = {"type": request.type}
            if request.token_hash:
                payload["token_hash"] = request.token_hash
                if request.email:
                    payload["email"] = request.email
            else:
                payload["email"] = request.email
                payload["token"] = request.token
            if request.captcha_token:
                payload["options"] = {"captcha_token": request.captcha_token}

            response = await asyncio.to_thread(
                self.client.auth.verify_otp,
                payload,
            )
            return self._format_auth_response(response)
        except ApiError:
            raise
        except SupabaseAuthException as exc:
            self._raise_provider_error(exc, operation="verify-otp")
        except Exception as exc:
            raise AuthUnavailableError() from exc

    async def reset_password_for_email(self, request: AuthForgotPasswordRequest) -> dict:
        try:
            options = {}
            if self.recovery_redirect_url:
                options["redirect_to"] = self.recovery_redirect_url
            if request.captcha_token:
                options["captcha_token"] = request.captcha_token
            await asyncio.to_thread(
                self.client.auth.reset_password_for_email,
                request.email,
                options=options or None,
            )
            return {"message": "Enlace de recuperación enviado al correo exitosamente."}
        except ApiError:
            raise
        except SupabaseAuthException as exc:
            self._raise_provider_error(exc, operation="forgot-password")
        except Exception as exc:
            raise AuthUnavailableError() from exc

    async def update_user_password(self, jwt_token: str, request: AuthUpdatePasswordRequest) -> dict:
        try:
            # Llamamos a _request del cliente auth pasando el jwt especificado del usuario
            response = await asyncio.to_thread(
                self.client.auth._request,
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
        except ApiError:
            raise
        except SupabaseAuthException as exc:
            self._raise_provider_error(exc, operation="update-password")
        except Exception as exc:
            raise AuthUnavailableError() from exc

    async def get_user(self, jwt_token: str) -> dict | None:
        try:
            user_response = await asyncio.to_thread(
                self.client.auth.get_user,
                jwt_token,
            )
            if not user_response or not user_response.user:
                return None
            user = user_response.user
            return {
                "id": str(user.id),
                "email": user.email,
                "user_metadata": user.user_metadata or {},
            }
        except AuthApiError as exc:
            if exc.status in {400, 401, 403}:
                return None
            self._raise_provider_error(exc, operation="get-user")
        except SupabaseAuthException as exc:
            self._raise_provider_error(exc, operation="get-user")
        except Exception as exc:
            raise AuthUnavailableError() from exc

    async def sign_out(self, jwt_token: str) -> None:
        try:
            await asyncio.to_thread(
                self.client.auth._request,
                "POST",
                "logout",
                jwt=jwt_token,
            )
        except AuthApiError as exc:
            if exc.status in {400, 401, 403}:
                return
            self._raise_provider_error(exc, operation="logout")
        except SupabaseAuthException as exc:
            self._raise_provider_error(exc, operation="logout")
        except Exception as exc:
            raise AuthUnavailableError() from exc

    def _raise_provider_error(
        self,
        exc: SupabaseAuthException,
        *,
        operation: str,
    ) -> NoReturn:
        status = int(getattr(exc, "status", 0) or 0)
        raw_code = getattr(exc, "code", None)
        code = str(getattr(raw_code, "value", raw_code) or "")

        if status == 429 or code in {
            "over_email_send_rate_limit",
            "over_request_rate_limit",
        }:
            raise AuthRateLimitError() from exc

        if status >= 500 or isinstance(exc, AuthRetryableError):
            raise AuthUnavailableError() from exc

        if operation == "login":
            raise InvalidCredentialsError() from exc
        if operation == "verify-otp":
            if code == "otp_expired":
                raise UnauthorizedError(
                    "El código OTP es incorrecto, expiró o ya fue utilizado. Solicita uno nuevo."
                ) from exc
            if code in {"flow_state_expired", "flow_state_not_found"}:
                raise UnauthorizedError(
                    "El enlace de acceso expiró o ya fue utilizado. Solicita uno nuevo."
                ) from exc
            raise UnauthorizedError("Código o token inválido o expirado.") from exc
        if operation in {"update-password", "get-user", "logout"} and status in {
            400,
            401,
            403,
        }:
            raise UnauthorizedError() from exc
        if code == "weak_password":
            raise AuthError("La contraseña no cumple la política de seguridad.") from exc

        safe_messages = {
            "register": "No fue posible completar el registro.",
            "send-otp": "No fue posible enviar el código de acceso.",
            "forgot-password": "No fue posible procesar la recuperación de contraseña.",
            "update-password": "No fue posible actualizar la contraseña.",
            "get-user": "No fue posible validar la sesión.",
            "logout": "No fue posible cerrar la sesión.",
        }
        raise AuthError(safe_messages.get(operation, "Error en autenticación.")) from exc

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
