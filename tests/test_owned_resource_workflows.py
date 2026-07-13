from __future__ import annotations

import asyncio
from types import SimpleNamespace
from uuid import UUID

import pytest
from pydantic import ValidationError

from app.domain.schemas.entities import NotebookCreate, RoomCreate
from app.domain.schemas.resources.notebooks import NotebookRepositoryCreateRequest
from app.domain.schemas.resources.rooms import (
    AddRoomNotebookRequest,
    RoomNotebookRepositoryCreateRequest,
    RoomRepositoryCreateRequest,
)
from app.infra.repositories.notebooks import NotebookRepository
from app.infra.repositories.rooms import RoomNotebookRepository, RoomRepository


NOTEBOOK_ID = UUID("00000000-0000-0000-0000-000000000001")
ROOM_ID = UUID("00000000-0000-0000-0000-000000000002")


class FakeRpcQuery:
    def __init__(self, data: dict) -> None:
        self.data = data

    def execute(self):
        return SimpleNamespace(data=self.data)


class FakeClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    def rpc(self, function_name: str, params: dict) -> FakeRpcQuery:
        self.calls.append((function_name, params))
        if function_name == "create_personal_notebook":
            return FakeRpcQuery({"notebook_id": str(NOTEBOOK_ID), "name": "Álgebra"})
        if function_name == "create_study_room":
            return FakeRpcQuery({"room_id": str(ROOM_ID), "name": "Grupo"})
        return FakeRpcQuery(
            {
                "room_id": str(ROOM_ID),
                "notebook_id": str(NOTEBOOK_ID),
                "created_by": "server-derived",
            }
        )


def test_notebook_and_room_creation_use_atomic_actor_derived_rpcs() -> None:
    client = FakeClient()
    notebook_repository = NotebookRepository(client)
    room_repository = RoomRepository(client)

    notebook = asyncio.run(
        notebook_repository.create(
            NotebookRepositoryCreateRequest(payload=NotebookCreate(name="Álgebra"))
        )
    )
    room = asyncio.run(
        room_repository.create(
            RoomRepositoryCreateRequest(payload=RoomCreate(name="Grupo"))
        )
    )

    assert notebook["notebook_id"] == str(NOTEBOOK_ID)
    assert room["room_id"] == str(ROOM_ID)
    assert client.calls == [
        ("create_personal_notebook", {"p_name": "Álgebra"}),
        ("create_study_room", {"p_name": "Grupo"}),
    ]


def test_room_notebook_creator_cannot_be_supplied_by_client() -> None:
    with pytest.raises(ValidationError):
        AddRoomNotebookRequest.model_validate(
            {"notebook_id": str(NOTEBOOK_ID), "created_by": str(ROOM_ID)}
        )

    client = FakeClient()
    repository = RoomNotebookRepository(client)
    asyncio.run(
        repository.create(
            RoomNotebookRepositoryCreateRequest(
                room_id=ROOM_ID,
                notebook_id=NOTEBOOK_ID,
            )
        )
    )

    assert client.calls == [
        (
            "attach_room_notebook",
            {
                "p_room_id": str(ROOM_ID),
                "p_notebook_id": str(NOTEBOOK_ID),
            },
        )
    ]


def test_notebook_statistics_fields_are_server_controlled() -> None:
    for field, value in (
        ("grade", 100),
        ("is_dominated", True),
        ("spent_time", 3600),
        ("last_seen_at", "2026-07-13T00:00:00Z"),
    ):
        with pytest.raises(ValidationError):
            NotebookCreate.model_validate({"name": "Seguro", field: value})
