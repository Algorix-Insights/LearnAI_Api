from __future__ import annotations

import asyncio
from types import SimpleNamespace
from uuid import UUID

import pytest

from app.core.exceptions import RepositoryError, ResourceNotFoundError
from app.domain.schemas.resources.notebooks import NotebookTagRepositoryCreateRequest
from app.infra.repositories.notebooks import NotebookTagRepository


NOTEBOOK_ID = UUID("00000000-0000-0000-0000-000000000001")
TAG_ID = UUID("00000000-0000-0000-0000-000000000002")


class PostgrestFailure(Exception):
    def __init__(self, code: str) -> None:
        self.code = code


class FakeQuery:
    def __init__(self, *, data=None, error: Exception | None = None) -> None:
        self.data = data or []
        self.error = error
        self.payload = None

    def insert(self, payload):
        self.payload = payload
        return self

    def execute(self):
        if self.error is not None:
            raise self.error
        return SimpleNamespace(data=self.data)


class FakeClient:
    def __init__(self, query: FakeQuery) -> None:
        self.query = query

    def table(self, table_name: str) -> FakeQuery:
        assert table_name == "notebook_tags"
        return self.query


def request() -> NotebookTagRepositoryCreateRequest:
    return NotebookTagRepositoryCreateRequest(
        notebook_id=NOTEBOOK_ID,
        tag_id=TAG_ID,
    )


def test_notebook_tag_create_returns_inserted_relationship() -> None:
    query = FakeQuery(data=[{"notebook_id": str(NOTEBOOK_ID), "tag_id": str(TAG_ID)}])

    result = asyncio.run(NotebookTagRepository(FakeClient(query)).create(request()))

    assert result == {"notebook_id": str(NOTEBOOK_ID), "tag_id": str(TAG_ID)}
    assert query.payload == result


def test_notebook_tag_create_is_idempotent_on_duplicate() -> None:
    query = FakeQuery(error=PostgrestFailure("23505"))

    result = asyncio.run(NotebookTagRepository(FakeClient(query)).create(request()))

    assert result == {"notebook_id": str(NOTEBOOK_ID), "tag_id": str(TAG_ID)}


@pytest.mark.parametrize("code", ["23503", "42501"])
def test_notebook_tag_create_hides_missing_or_forbidden_resources(code: str) -> None:
    repository = NotebookTagRepository(FakeClient(FakeQuery(error=PostgrestFailure(code))))

    with pytest.raises(ResourceNotFoundError):
        asyncio.run(repository.create(request()))


def test_notebook_tag_create_keeps_unexpected_storage_errors_as_500() -> None:
    repository = NotebookTagRepository(FakeClient(FakeQuery(error=PostgrestFailure("XX000"))))

    with pytest.raises(RepositoryError) as exc_info:
        asyncio.run(repository.create(request()))

    assert exc_info.value.status_code == 500
    assert exc_info.value.message == "No se pudo crear el registro."
