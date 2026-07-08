from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass
import re
from typing import Any
from urllib.parse import parse_qsl, urlencode


MAX_LIMIT = 500
DEFAULT_LIMIT = 100
DEFAULT_OFFSET = 0
PAGINATION_KEYS = {"limit", "offset", "page", "per_page"}
FILTER_OPERATORS = {"eq", "neq", "gt", "gte", "lt", "lte", "like", "ilike", "in", "is"}
FIELD_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class QueryParamError(ValueError):
    pass


@dataclass(frozen=True)
class ApiFilter:
    field: str
    operator: str
    value: Any


@dataclass(frozen=True)
class ApiQueryParams:
    limit: int = DEFAULT_LIMIT
    offset: int = DEFAULT_OFFSET
    filters: tuple[ApiFilter, ...] = ()
    raw_pairs: tuple[tuple[str, str], ...] = ()

    def normalized_query_string(self) -> bytes:
        pairs = [(key, value) for key, value in self.raw_pairs if key not in {"limit", "offset"}]
        pairs.extend([("limit", str(self.limit)), ("offset", str(self.offset))])
        return urlencode(pairs, doseq=True).encode()


_api_query_params: ContextVar[ApiQueryParams | None] = ContextVar(
    "api_query_params", default=None
)


def get_api_query_params() -> ApiQueryParams | None:
    return _api_query_params.get()


def set_api_query_params(params: ApiQueryParams):
    return _api_query_params.set(params)


def reset_api_query_params(token: object) -> None:
    _api_query_params.reset(token)


def parse_api_query_params(query_string: bytes | str) -> ApiQueryParams:
    raw_query = query_string.decode() if isinstance(query_string, bytes) else query_string
    pairs = tuple(parse_qsl(raw_query, keep_blank_values=True))
    values = dict(pairs)

    page = _optional_int(values.get("page"), "page", minimum=1)
    per_page = _optional_int(values.get("per_page"), "per_page", minimum=1, maximum=MAX_LIMIT)

    if page is not None or per_page is not None:
        effective_page = page or 1
        limit = per_page or _int_value(values.get("limit"), "limit", DEFAULT_LIMIT, 1, MAX_LIMIT)
        offset = (effective_page - 1) * limit
    else:
        limit = _int_value(values.get("limit"), "limit", DEFAULT_LIMIT, 1, MAX_LIMIT)
        offset = _int_value(values.get("offset"), "offset", DEFAULT_OFFSET, 0, None)

    return ApiQueryParams(
        limit=limit,
        offset=offset,
        filters=tuple(_parse_filter(key, value) for key, value in pairs if key not in PAGINATION_KEYS),
        raw_pairs=pairs,
    )


def _parse_filter(key: str, value: str) -> ApiFilter:
    field, separator, operator = key.partition("__")
    operator = operator if separator else "eq"

    if not FIELD_PATTERN.fullmatch(field):
        raise QueryParamError(f"Filtro invalido: {key}.")
    if operator not in FILTER_OPERATORS:
        raise QueryParamError(f"Operador de filtro invalido: {operator}.")

    parsed_value: Any = value
    if operator == "in":
        parsed_value = [item for item in value.split(",") if item != ""]
        if not parsed_value:
            raise QueryParamError(f"Filtro invalido: {key}.")
    if operator == "is":
        parsed_value = value.lower()
        if parsed_value not in {"null", "true", "false"}:
            raise QueryParamError(f"Filtro invalido: {key}.")

    return ApiFilter(field=field, operator=operator, value=parsed_value)


def _optional_int(
    value: str | None, name: str, minimum: int, maximum: int | None = None
) -> int | None:
    if value is None:
        return None
    return _int_value(value, name, 0, minimum, maximum)


def _int_value(
    value: str | None,
    name: str,
    default: int,
    minimum: int,
    maximum: int | None,
) -> int:
    if value is None:
        return default
    try:
        parsed = int(value)
    except ValueError as exc:
        raise QueryParamError(f"{name} debe ser entero.") from exc

    if parsed < minimum:
        raise QueryParamError(f"{name} debe ser mayor o igual a {minimum}.")
    if maximum is not None and parsed > maximum:
        raise QueryParamError(f"{name} debe ser menor o igual a {maximum}.")
    return parsed
