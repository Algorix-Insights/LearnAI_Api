from typing import Any

from fastapi.testclient import TestClient

from app.api.dependencies import get_users_use_case
from app.application.usecases import UserUseCase
from app.domain.schemas.aggregate import (
    RepositoryCreateItemRequest,
    RepositoryItemRequest,
    RepositoryListItemsRequest,
    RepositoryUpdateItemRequest,
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
                }
            ]
        }

    async def list(self, request: RepositoryListItemsRequest) -> list[dict[str, Any]]:
        return self.data["users"][request.offset : request.offset + request.limit]

    async def get(self, request: RepositoryItemRequest) -> dict[str, Any] | None:
        for item in self.data["users"]:
            if item["user_id"] == request.item_id:
                return item
        return None

    async def create(self, request: RepositoryCreateItemRequest) -> dict[str, Any]:
        item = {"user_id": "00000000-0000-0000-0000-000000000002", **request.payload}
        self.data["users"].append(item)
        return item

    async def update(self, request: RepositoryUpdateItemRequest) -> dict[str, Any] | None:
        item = await self.get(RepositoryItemRequest(item_id=request.item_id))
        if item is not None:
            item.update(request.payload)
        return item

    async def delete(self, request: RepositoryItemRequest) -> dict[str, Any] | None:
        return await self.get(request)


def test_crud_hides_sensitive_fields_and_uses_spanish_errors() -> None:
    repository = FakeCrudRepository()
    app.dependency_overrides[get_users_use_case] = lambda: UserUseCase(repository)
    client = TestClient(app)

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
    assert create_response.status_code == 201
    assert "hash_password" not in create_response.json()["data"]

    invalid_response = client.post("/api/v1/users", json={"name": "Incomplete"})
    assert invalid_response.status_code == 422
    assert invalid_response.json()["detail"] == "La solicitud no es valida."

    missing_response = client.get("/api/v1/users/00000000-0000-0000-0000-000000000099")
    assert missing_response.status_code == 404
    assert missing_response.json()["detail"] == "Recurso no encontrado."

    app.dependency_overrides.clear()
