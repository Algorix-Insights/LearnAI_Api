from types import SimpleNamespace
from typing import Any

from fastapi.testclient import TestClient

from app.api import auth_rate_limit as auth_rate_limit_module
from app.api.auth_rate_limit import clear_auth_rate_limits
from app.api.dependencies import get_auth_use_case, get_users_use_case
from app.application.usecases.auth import AuthUseCase
from app.application.usecases.users import UserUseCase
from app.core.exceptions import AuthError, InvalidCredentialsError, UnauthorizedError
from app.domain.schemas.resources.auth import (
    AuthForgotPasswordRequest,
    AuthLoginRequest,
    AuthOtpRequest,
    AuthRegisterRequest,
    AuthUpdatePasswordRequest,
    AuthVerifyOtpRequest,
)
from app.domain.schemas.resources.users import (
    UserRepositoryCreateRequest,
    UserRepositoryDeleteRequest,
    UserRepositoryGetRequest,
    UserRepositoryListRequest,
    UserRepositoryUpdateRequest,
)
from app.main import app


class FakeUserRepository:
    def __init__(self) -> None:
        self.data: dict[str, list[dict[str, Any]]] = {
            "users": [
                {
                    "user_id": "00000000-0000-0000-0000-000000000001",
                    "name": "Ada",
                    "last_name": "Lovelace",
                    "email": "ada@example.test",
                    "hash_password": "secret",
                }
            ]
        }

    async def list(self, request: UserRepositoryListRequest) -> list[dict[str, Any]]:
        return self.data["users"]

    async def get(self, request: UserRepositoryGetRequest) -> dict[str, Any] | None:
        for item in self.data["users"]:
            if item["user_id"] == str(request.user_id):
                return item
        return None

    async def create(self, request: UserRepositoryCreateRequest) -> dict[str, Any]:
        payload = request.payload.model_dump(exclude_unset=True, mode="json")
        item = {"user_id": payload.get("user_id") or "00000000-0000-0000-0000-000000000002", **payload}
        self.data["users"].append(item)
        return item

    async def update(self, request: UserRepositoryUpdateRequest) -> dict[str, Any] | None:
        item = await self.get(UserRepositoryGetRequest(user_id=request.user_id))
        if item is not None:
            item.update(request.payload.model_dump(exclude_unset=True, mode="json"))
        return item

    async def delete(self, request: UserRepositoryDeleteRequest) -> dict[str, Any] | None:
        return await self.get(UserRepositoryGetRequest(user_id=request.user_id))


class FakeAuthRepository:
    def __init__(self) -> None:
        self.users = {
            "ada@example.test": {
                "id": "00000000-0000-0000-0000-000000000001",
                "email": "ada@example.test",
                "password": "secret_password",
                "user_metadata": {"name": "Ada", "last_name": "Lovelace"},
            }
        }
        self.tokens = {
            "valid_token_ada": "00000000-0000-0000-0000-000000000001",
        }

    async def sign_up(self, request: AuthRegisterRequest) -> dict:
        if request.email in self.users:
            raise AuthError("El correo electrónico ya está registrado.")
        if not request.password:
            return {
                "access_token": "",
                "refresh_token": None,
                "token_type": "bearer",
                "expires_in": None,
                "user": {
                    "id": "",
                    "email": request.email,
                    "user_metadata": {"name": request.name, "last_name": request.last_name},
                },
                "message": "Registro iniciado. Revisa tu correo para verificar y entrar con el Magic Link o código OTP.",
            }
        user_id = "00000000-0000-0000-0000-000000000010"
        self.users[request.email] = {
            "id": user_id,
            "email": request.email,
            "password": request.password,
            "user_metadata": {"name": request.name, "last_name": request.last_name},
        }
        token = f"token_{request.email}"
        self.tokens[token] = user_id
        return {
            "access_token": token,
            "refresh_token": "refresh_" + token,
            "token_type": "bearer",
            "expires_in": 3600,
            "user": {
                "id": user_id,
                "email": request.email,
                "user_metadata": {"name": request.name, "last_name": request.last_name},
            },
        }

    async def sign_in_with_password(self, request: AuthLoginRequest) -> dict:
        user = self.users.get(request.email)
        if not user or user["password"] != request.password:
            raise InvalidCredentialsError()
        token = f"token_{request.email}"
        self.tokens[token] = user["id"]
        return {
            "access_token": token,
            "refresh_token": "refresh_" + token,
            "token_type": "bearer",
            "expires_in": 3600,
            "user": {
                "id": user["id"],
                "email": user["email"],
                "user_metadata": user["user_metadata"],
            },
        }

    async def sign_in_with_otp(self, request: AuthOtpRequest) -> dict:
        return {"message": "Código OTP / enlace enviado al correo exitosamente."}

    async def verify_otp(self, request: AuthVerifyOtpRequest) -> dict:
        if request.token == "valid_otp_code":
            user_id = "00000000-0000-0000-0000-000000000001"
            return {
                "access_token": "valid_token_ada",
                "refresh_token": "refresh_ada",
                "token_type": "bearer",
                "expires_in": 3600,
                "user": {
                    "id": user_id,
                    "email": "ada@example.test",
                    "user_metadata": {"name": "Ada", "last_name": "Lovelace"},
                },
            }
        raise UnauthorizedError("Código o token inválido o expirado.")

    async def reset_password_for_email(self, request: AuthForgotPasswordRequest) -> dict:
        return {"message": "Enlace de recuperación enviado al correo exitosamente."}

    async def update_user_password(self, jwt_token: str, request: AuthUpdatePasswordRequest) -> dict:
        user_id = self.tokens.get(jwt_token)
        if not user_id:
            raise UnauthorizedError("Token inválido.")
        for email, u in self.users.items():
            if u["id"] == user_id:
                u["password"] = request.password
                return {
                    "id": u["id"],
                    "email": u["email"],
                    "user_metadata": u["user_metadata"],
                }
        raise AuthError("Usuario no encontrado para actualizar contraseña.")

    async def get_user(self, jwt_token: str) -> dict | None:
        user_id = self.tokens.get(jwt_token)
        if not user_id:
            return None
        for email, u in self.users.items():
            if u["id"] == user_id:
                return {
                    "id": u["id"],
                    "email": u["email"],
                    "user_metadata": u["user_metadata"],
                }
        return None

    async def sign_out(self, jwt_token: str) -> None:
        self.tokens.pop(jwt_token, None)


def _setup_client() -> tuple[TestClient, FakeUserRepository, FakeAuthRepository]:
    user_repo = FakeUserRepository()
    auth_repo = FakeAuthRepository()
    app.dependency_overrides[get_users_use_case] = lambda: UserUseCase(user_repo)
    app.dependency_overrides[get_auth_use_case] = lambda: AuthUseCase(auth_repo, user_repo)
    return TestClient(app), user_repo, auth_repo


def test_auth_register_and_profile_sync() -> None:
    client, user_repo, auth_repo = _setup_client()

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.test",
            "password": "supersecretpassword",
            "name": "Marie",
            "last_name": "Curie",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["data"]["access_token"] == "token_newuser@example.test"
    assert body["data"]["user"]["email"] == "newuser@example.test"
    assert body["data"]["user"]["name"] == "Marie"
    assert "hash_password" not in body["data"]["user"]

    # Verificar que se creó en FakeUserRepository y se sincronizó correctamente con el mismo UUID
    sync_user = None
    for u in user_repo.data["users"]:
        if u["email"] == "newuser@example.test":
            sync_user = u
            break
    assert sync_user is not None
    assert sync_user["user_id"] == "00000000-0000-0000-0000-000000000010"
    app.dependency_overrides.clear()


def test_auth_login_success_and_failure() -> None:
    client, user_repo, auth_repo = _setup_client()

    # Login exitoso
    success_response = client.post(
        "/api/v1/auth/login",
        json={"email": "ada@example.test", "password": "secret_password"},
    )
    assert success_response.status_code == 200
    assert success_response.json()["data"]["access_token"] == "token_ada@example.test"

    # Login fallido (contraseña errónea)
    fail_response = client.post(
        "/api/v1/auth/login",
        json={"email": "ada@example.test", "password": "wrong_password"},
    )
    assert fail_response.status_code == 401
    assert fail_response.json()["detail"] == "Credenciales incorrectas."
    app.dependency_overrides.clear()


def test_auth_rate_limit_is_disabled_by_default(monkeypatch) -> None:
    clear_auth_rate_limits()
    monkeypatch.setattr(
        auth_rate_limit_module,
        "get_settings",
        lambda: SimpleNamespace(auth_rate_limit_enabled=False),
    )
    client, _, _ = _setup_client()

    for _ in range(25):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "ada@example.test", "password": "secret_password"},
        )
        assert response.status_code == 200

    clear_auth_rate_limits()
    app.dependency_overrides.clear()


def test_auth_otp_flow() -> None:
    client, _, _ = _setup_client()

    # Enviar OTP / Magic link
    send_response = client.post(
        "/api/v1/auth/otp",
        json={"email": "ada@example.test"},
    )
    assert send_response.status_code == 200
    assert "Código OTP" in send_response.json()["data"]["message"]

    # Verificar OTP exitoso
    verify_response = client.post(
        "/api/v1/auth/verify-otp",
        json={"email": "ada@example.test", "token": "valid_otp_code"},
    )
    assert verify_response.status_code == 200
    assert verify_response.json()["data"]["access_token"] == "valid_token_ada"

    # Verificar OTP fallido
    verify_fail = client.post(
        "/api/v1/auth/verify-otp",
        json={"email": "ada@example.test", "token": "invalid_code"},
    )
    assert verify_fail.status_code == 401
    app.dependency_overrides.clear()


def test_auth_forgot_and_reset_password() -> None:
    client, _, auth_repo = _setup_client()

    # Solicitar recuperación
    forgot_resp = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "ada@example.test"},
    )
    assert forgot_resp.status_code == 200

    # Cambiar contraseña con sesión/header
    reset_resp = client.post(
        "/api/v1/auth/reset-password",
        json={"password": "new_secret_password"},
        headers={"Authorization": "Bearer valid_token_ada"},
    )
    assert reset_resp.status_code == 200
    assert auth_repo.users["ada@example.test"]["password"] == "new_secret_password"

    # Cambiar contraseña sin header -> 401
    unauth_reset = client.post(
        "/api/v1/auth/reset-password",
        json={"password": "new_secret_password"},
    )
    assert unauth_reset.status_code == 401
    app.dependency_overrides.clear()


def test_auth_get_me_and_logout() -> None:
    client, _, _ = _setup_client()

    # Obtener /me con token válido
    me_resp = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer valid_token_ada"})
    assert me_resp.status_code == 200
    assert me_resp.json()["data"]["email"] == "ada@example.test"

    # Obtener /me sin token -> 401
    me_unauth = client.get("/api/v1/auth/me")
    assert me_unauth.status_code == 401

    # Logout
    logout_resp = client.post("/api/v1/auth/logout", headers={"Authorization": "Bearer valid_token_ada"})
    assert logout_resp.status_code == 200

    # Tras hacer logout, el token ya no es válido para /me en el fake repo
    me_after_logout = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer valid_token_ada"})
    assert me_after_logout.status_code == 401
    app.dependency_overrides.clear()


def test_auth_register_without_password() -> None:
    client, _, _ = _setup_client()

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "passwordless@example.test",
            "name": "Nikola",
            "last_name": "Tesla",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["data"]["access_token"] == ""
    assert "Registro iniciado" in body["data"]["message"]
    assert body["data"]["user"] is None
    app.dependency_overrides.clear()


def test_auth_account_limit_cannot_be_bypassed_with_padded_json(monkeypatch) -> None:
    clear_auth_rate_limits()
    monkeypatch.setattr(
        auth_rate_limit_module,
        "get_settings",
        lambda: SimpleNamespace(auth_rate_limit_enabled=True),
    )
    client, _, _ = _setup_client()
    payload = (
        '{"email":"ada@example.test","should_create_user":false}'
        + (" " * 16_384)
    )

    response = client.post(
        "/api/v1/auth/otp",
        content=payload,
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 413
    clear_auth_rate_limits()
    app.dependency_overrides.clear()


def test_suspended_profile_cannot_use_valid_supabase_token() -> None:
    client, user_repo, _ = _setup_client()
    user_repo.data["users"][0]["status"] = "suspended"

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer valid_token_ada"},
    )

    assert response.status_code == 403
    app.dependency_overrides.clear()
