import asyncio
from typing import Any

from app.core.query import parse_api_query_params, reset_api_query_params, set_api_query_params
from app.infra.repositories.base import BaseSupabaseRepository


class FakeQuery:
    def __init__(self) -> None:
        self.calls: list[tuple[str, Any, Any]] = []

    def select(self, value: str):
        self.calls.append(("select", value, None))
        return self

    def eq(self, field: str, value: Any):
        self.calls.append(("eq", field, value))
        return self

    def gte(self, field: str, value: Any):
        self.calls.append(("gte", field, value))
        return self

    def range(self, start: int, end: int):
        self.calls.append(("range", start, end))
        return self

    def execute(self):
        return type("Response", (), {"data": []})()


class FakeClient:
    def __init__(self) -> None:
        self.query = FakeQuery()

    def table(self, table_name: str):
        self.query.calls.append(("table", table_name, None))
        return self.query


def test_query_parser_normalizes_pagination_and_filters() -> None:
    params = parse_api_query_params("page=2&per_page=25&status=active&grade__gte=3")

    assert params.limit == 25
    assert params.offset == 25
    assert [(item.field, item.operator, item.value) for item in params.filters] == [
        ("status", "eq", "active"),
        ("grade", "gte", "3"),
    ]


def test_base_repository_applies_context_query_to_supabase() -> None:
    client = FakeClient()
    repository = BaseSupabaseRepository(client=client)
    token = set_api_query_params(
        parse_api_query_params("page=2&per_page=10&status=active&grade__gte=3")
    )

    try:
        asyncio.run(repository._list("notebooks", limit=100, offset=0))
    finally:
        reset_api_query_params(token)

    assert client.query.calls == [
        ("table", "notebooks", None),
        ("select", "*", None),
        ("eq", "status", "active"),
        ("gte", "grade", "3"),
        ("range", 10, 19),
    ]
