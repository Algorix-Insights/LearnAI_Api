from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel

from app.core.exceptions import EmptyPayloadError, ResourceNotFoundError
from app.domain.aggregates import AggregateDefinition
from app.domain.interfaces import AggregateRepository
from app.domain.schemas.aggregate import (
    CreateItemRequest,
    DeleteItemRequest,
    ItemRequest,
    ListItemsRequest,
    RepositoryCreateItemRequest,
    RepositoryItemRequest,
    RepositoryListItemsRequest,
    RepositoryUpdateItemRequest,
    UpdateItemRequest,
)
from app.domain.schemas.crud import CrudItemResponse, CrudListResponse


class AggregateCrudUseCase:
    def __init__(self, definition: AggregateDefinition, repository: AggregateRepository) -> None:
        self.definition = definition
        self.repository = repository

    async def list(self, request: ListItemsRequest) -> CrudListResponse:
        data = await self.repository.list(
            RepositoryListItemsRequest(limit=request.limit, offset=request.offset)
        )
        return CrudListResponse(
            data=[self._hide_fields(item) for item in data],
            limit=request.limit,
            offset=request.offset,
        )

    async def get(self, request: ItemRequest) -> CrudItemResponse:
        data = await self.repository.get(RepositoryItemRequest(item_id=request.item_id))
        if data is None:
            raise ResourceNotFoundError()
        return CrudItemResponse(data=self._hide_fields(data))

    async def create(self, request: CreateItemRequest) -> CrudItemResponse:
        payload = self._validate_payload(self.definition.create_schema, request.payload)
        data = await self.repository.create(RepositoryCreateItemRequest(payload=payload))
        return CrudItemResponse(data=self._hide_fields(data))

    async def update(self, request: UpdateItemRequest) -> CrudItemResponse:
        payload = self._validate_payload(self.definition.update_schema, request.payload)
        if not payload:
            raise EmptyPayloadError()
        if self.definition.updated_at_field is not None:
            payload[self.definition.updated_at_field] = datetime.now(UTC).isoformat()
        data = await self.repository.update(
            RepositoryUpdateItemRequest(item_id=request.item_id, payload=payload)
        )
        if data is None:
            raise ResourceNotFoundError()
        return CrudItemResponse(data=self._hide_fields(data))

    async def delete(self, request: DeleteItemRequest) -> CrudItemResponse:
        data = await self.repository.delete(RepositoryItemRequest(item_id=request.item_id))
        if data is None:
            raise ResourceNotFoundError()
        return CrudItemResponse(data=self._hide_fields(data))

    def _validate_payload(self, schema: type[BaseModel], payload: BaseModel) -> dict[str, Any]:
        return schema.model_validate(payload.model_dump()).model_dump(
            exclude_unset=True,
            mode="json",
        )

    def _hide_fields(self, item: dict[str, Any]) -> dict[str, Any]:
        if not self.definition.hidden_fields:
            return item
        return {
            key: value
            for key, value in item.items()
            if key not in self.definition.hidden_fields
        }
