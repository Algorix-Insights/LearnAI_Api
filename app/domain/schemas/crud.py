from typing import Any

from pydantic import BaseModel, ConfigDict


class CrudSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CrudItemResponse(CrudSchema):
    data: dict[str, Any]


class CrudListResponse(CrudSchema):
    data: list[dict[str, Any]]
    limit: int
    offset: int
