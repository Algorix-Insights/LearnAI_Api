from typing import Any

from fastapi.testclient import TestClient

from app.api.dependencies import get_current_user, get_users_use_case
from app.application.usecases import UserUseCase
from app.core.query import get_api_query_params
from app.domain.schemas.resources.users import (
    UserRepositoryCreateRequest,
    UserRepositoryDeleteRequest,
    UserRepositoryGetRequest,
    UserRepositoryListRequest,
    UserRepositoryUpdateRequest,
    UserRead,
)
from app.main import app


class FakeCrudRepository:
    def __init__(self) -> None:
        self.data: dict[str, list[dict[str, Any]]] = {
            "users": [
                {
                    "user_id": "00000000-0000-0000-0000-000000000001",
                    "name": "Ada",
                    "last_name": "Lovelace",
                    "email": "ada@example.test",
                    "hash_password": "secret",
                },
                {
                    "user_id": "00000000-0000-0000-0000-000000000003",
                    "name": "Linus",
                    "last_name": "Torvalds",
                    "email": "linus@example.test",
                    "hash_password": "secret",
                }
            ]
        }

    async def list(self, request: UserRepositoryListRequest) -> list[dict[str, Any]]:
        items = self.data["users"]
        api_query = get_api_query_params()
        if api_query is not None:
            for item_filter in api_query.filters:
                if item_filter.operator == "eq":
                    items = [
                        item for item in items if str(item.get(item_filter.field)) == item_filter.value
                    ]
        return items[request.offset : request.offset + request.limit]

    async def get(self, request: UserRepositoryGetRequest) -> dict[str, Any] | None:
        for item in self.data["users"]:
            if item["user_id"] == str(request.user_id):
                return item
        return None

    async def create(self, request: UserRepositoryCreateRequest) -> dict[str, Any]:
        payload = request.payload.model_dump(exclude_unset=True, mode="json")
        item = {"user_id": "00000000-0000-0000-0000-000000000002", **payload}
        self.data["users"].append(item)
        return item

    async def update(self, request: UserRepositoryUpdateRequest) -> dict[str, Any] | None:
        item = await self.get(UserRepositoryGetRequest(user_id=request.user_id))
        if item is not None:
            item.update(request.payload.model_dump(exclude_unset=True, mode="json"))
        return item

    async def delete(self, request: UserRepositoryDeleteRequest) -> dict[str, Any] | None:
        return await self.get(UserRepositoryGetRequest(user_id=request.user_id))


def test_users_surface_is_self_only_and_account_creation_is_auth_owned() -> None:
    repository = FakeCrudRepository()
    app.dependency_overrides[get_users_use_case] = lambda: UserUseCase(repository)
    app.dependency_overrides[get_current_user] = lambda: UserRead(
        user_id="00000000-0000-0000-0000-000000000001",
        email="ada@example.test",
    )
    client = TestClient(app, headers={"Authorization": "Bearer test-token"})

    list_response = client.get("/api/v1/users")
    assert list_response.status_code == 200
    assert "hash_password" not in list_response.json()["data"][0]

    create_response = client.post(
        "/api/v1/users",
        json={
            "name": "Grace",
            "last_name": "Hopper",
            "email": "grace@example.test",
            "hash_password": "secret",
        },
    )
    assert create_response.status_code == 405

    invalid_response = client.post("/api/v1/users", json={"name": "Incomplete"})
    assert invalid_response.status_code == 405

    missing_response = client.get("/api/v1/users/00000000-0000-0000-0000-000000000099")
    assert missing_response.status_code == 404
    assert missing_response.json()["detail"] == "Recurso no encontrado."

    app.dependency_overrides.clear()


def test_users_list_never_enumerates_other_profiles() -> None:
    repository = FakeCrudRepository()
    app.dependency_overrides[get_users_use_case] = lambda: UserUseCase(repository)
    app.dependency_overrides[get_current_user] = lambda: UserRead(
        user_id="00000000-0000-0000-0000-000000000001",
        email="ada@example.test",
    )
    client = TestClient(app, headers={"Authorization": "Bearer test-token"})

    response = client.get("/api/v1/users?page=1&per_page=1&name=Linus")

    assert response.status_code == 200
    body = response.json()
    assert body["limit"] == 1
    assert body["offset"] == 0
    assert [item["user_id"] for item in body["data"]] == [
        "00000000-0000-0000-0000-000000000001"
    ]

    app.dependency_overrides.clear()


def test_crud_rejects_invalid_core_pagination() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/users?limit=0")

    assert response.status_code == 422
    assert response.json()["detail"] == "La solicitud no es valida."
