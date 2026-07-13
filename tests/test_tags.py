from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api.dependencies import get_current_user, get_tags_use_case
from app.application.usecases.tags import TagUseCase
from app.core.exceptions import ApiError
from app.domain.schemas.entities import TagCreate
from app.domain.schemas.resources.tags import (
    TagCreateRequest,
    TagListRequest,
    TagRepositoryCreateRequest,
    TagRepositoryListRequest,
)
from app.domain.schemas.resources.users import UserRead
from app.infra.repositories.tags import TagRepository
from app.main import app


USER_ID = UUID("00000000-0000-0000-0000-000000000001")
OTHER_USER_ID = UUID("00000000-0000-0000-0000-000000000002")
TAG_ID = UUID("00000000-0000-0000-0000-000000000010")


class FakeTagRepository:
    def __init__(self) -> None:
        self.list_request = None
        self.create_request = None

    async def list(self, request):
        self.list_request = request
        return [
            {
                "id": str(TAG_ID),
                "name": "Álgebra",
                "status": "active",
                "scope": "system",
            }
        ]

    async def create(self, request):
        self.create_request = request
        return {
            "id": str(TAG_ID),
            "name": request.payload.name,
            "status": "active",
            "scope": "user",
        }


def test_tag_routes_use_jwt_actor_and_create_returns_201() -> None:
    repository = FakeTagRepository()
    use_case = TagUseCase(repository)
    app.dependency_overrides[get_current_user] = lambda: UserRead(user_id=USER_ID)
    app.dependency_overrides[get_tags_use_case] = lambda: use_case
    client = TestClient(app, headers={"Authorization": "Bearer test-token"})

    listed = client.get("/api/v1/tags?limit=25&offset=0")
    created = client.post("/api/v1/tags", json={"name": "  Matemáticas  "})

    assert listed.status_code == 200
    assert listed.json()["data"][0]["name"] == "Álgebra"
    assert listed.json()["data"][0]["scope"] == "system"
    assert repository.list_request.user_id == USER_ID
    assert created.status_code == 201
    assert created.json()["data"]["name"] == "Matemáticas"
    assert created.json()["data"]["scope"] == "user"
    assert repository.create_request.user_id == USER_ID
    app.dependency_overrides.clear()


def test_tag_create_rejects_client_supplied_owner() -> None:
    repository = FakeTagRepository()
    app.dependency_overrides[get_current_user] = lambda: UserRead(user_id=USER_ID)
    app.dependency_overrides[get_tags_use_case] = lambda: TagUseCase(repository)
    client = TestClient(app, headers={"Authorization": "Bearer test-token"})

    response = client.post(
        "/api/v1/tags",
        json={"name": "Privada", "created_by_user_id": str(OTHER_USER_ID)},
    )

    assert response.status_code == 422
    assert repository.create_request is None
    app.dependency_overrides.clear()


def test_tag_routes_require_authentication() -> None:
    client = TestClient(app)

    assert client.get("/api/v1/tags").status_code == 401
    assert client.post("/api/v1/tags", json={"name": "Privada"}).status_code == 401


def test_tag_use_case_forwards_actor_to_repository() -> None:
    repository = FakeTagRepository()
    use_case = TagUseCase(repository)

    asyncio.run(use_case.list(TagListRequest(limit=10), user_id=USER_ID))
    asyncio.run(
        use_case.create(
            TagCreateRequest(payload=TagCreate(name="Historia")),
            user_id=USER_ID,
        )
    )

    assert repository.list_request.user_id == USER_ID
    assert repository.create_request.user_id == USER_ID


class RecordingQuery:
    def __init__(self, data=None, error: Exception | None = None) -> None:
        self.calls: list[tuple] = []
        self.data = data or []
        self.error = error

    def select(self, columns):
        self.calls.append(("select", columns))
        return self

    def or_(self, filters):
        self.calls.append(("or", filters))
        return self

    def eq(self, column, value):
        self.calls.append(("eq", column, value))
        return self

    def order(self, column):
        self.calls.append(("order", column))
        return self

    def range(self, start, end):
        self.calls.append(("range", start, end))
        return self

    def insert(self, payload):
        self.calls.append(("insert", payload))
        return self

    def execute(self):
        if self.error is not None:
            raise self.error
        return SimpleNamespace(data=self.data)


class RecordingClient:
    def __init__(self, query: RecordingQuery) -> None:
        self.query = query

    def table(self, table_name):
        self.query.calls.append(("table", table_name))
        return self.query


def test_tag_repository_lists_only_global_and_actor_owned_tags() -> None:
    query = RecordingQuery(
        data=[
            {
                "id": str(TAG_ID),
                "name": "Global",
                "status": "active",
                "created_by_user_id": None,
            },
            {
                "id": "00000000-0000-0000-0000-000000000011",
                "name": "Propia",
                "status": "active",
                "created_by_user_id": str(USER_ID),
            },
        ]
    )
    repository = TagRepository(RecordingClient(query))

    result = asyncio.run(
        repository.list(TagRepositoryListRequest(limit=20, offset=0, user_id=USER_ID))
    )

    assert ("select", "id,name,status,created_by_user_id") in query.calls
    assert (
        "or",
        "created_by_user_id.is.null,created_by_user_id.eq.00000000-0000-0000-0000-000000000001",
    ) in query.calls
    assert ("eq", "status", "active") in query.calls
    assert [(call[0], call[1]) for call in query.calls if call[0] == "order"] == [
        ("order", "name"),
        ("order", "id"),
    ]
    assert [item["scope"] for item in result] == ["system", "user"]
    assert all("created_by_user_id" not in item for item in result)


def test_tag_repository_sets_owner_from_the_server_request() -> None:
    query = RecordingQuery(
        data=[
            {
                "id": str(TAG_ID),
                "name": "Historia",
                "status": "active",
                "created_by_user_id": str(USER_ID),
            }
        ]
    )
    repository = TagRepository(RecordingClient(query))

    result = asyncio.run(
        repository.create(
            TagRepositoryCreateRequest(
                payload=TagCreate(name="Historia"),
                user_id=USER_ID,
            )
        )
    )

    insert_call = next(call for call in query.calls if call[0] == "insert")
    assert insert_call[1]["created_by_user_id"] == str(USER_ID)
    assert [call for call in query.calls if call[0] == "table"] == [("table", "tags")]
    assert result["scope"] == "user"
    assert "created_by_user_id" not in result


class UniqueViolation(Exception):
    code = "23505"


def test_duplicate_tag_name_returns_conflict_instead_of_repository_500() -> None:
    repository = TagRepository(RecordingClient(RecordingQuery(error=UniqueViolation())))

    with pytest.raises(ApiError) as exc_info:
        asyncio.run(
            repository.create(
                TagRepositoryCreateRequest(
                    payload=TagCreate(name="Historia"),
                    user_id=USER_ID,
                )
            )
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.message == "Ya existe una tag con ese nombre."


def test_duplicate_tag_http_response_is_a_clear_conflict() -> None:
    repository = TagRepository(RecordingClient(RecordingQuery(error=UniqueViolation())))
    app.dependency_overrides[get_current_user] = lambda: UserRead(user_id=USER_ID)
    app.dependency_overrides[get_tags_use_case] = lambda: TagUseCase(repository)
    client = TestClient(app, headers={"Authorization": "Bearer test-token"})

    response = client.post("/api/v1/tags", json={"name": "Historia"})

    assert response.status_code == 409
    assert response.json() == {"detail": "Ya existe una tag con ese nombre."}
    app.dependency_overrides.clear()


def test_tag_create_only_accepts_active_tags() -> None:
    with pytest.raises(ValidationError):
        TagCreate(name="Archivada", status="inactive")


def test_user_owned_tags_migration_is_private_and_case_insensitive() -> None:
    migration = (
        Path(__file__).parents[1] / "supabase" / "migrations" / "20260713001300_user_owned_tags.sql"
    ).read_text(encoding="utf-8")

    assert "created_by_user_id IS NULL" in migration
    assert "created_by_user_id = (SELECT auth.uid())" in migration
    assert "status = 'active'" in migration
    assert "LOWER(BTRIM(name))" in migration
    assert "CHECK (name = BTRIM(name) AND name <> '') NOT VALID" in migration
    assert "GRANT INSERT (" in migration
    assert "learnia_tags_owner_insert" in migration
    assert "available_tag.id = notebook_tags.tag_id" in migration
