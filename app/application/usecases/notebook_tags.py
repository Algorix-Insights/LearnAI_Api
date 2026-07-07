from app.core.exceptions import ResourceNotFoundError
from app.domain.interfaces import CompositeRepository
from app.domain.schemas import NotebookTagPath
from app.domain.schemas.aggregate import RepositoryCreateItemRequest, RepositoryFilterRequest
from app.domain.schemas.crud import CrudItemResponse


class NotebookTagUseCase:
    def __init__(self, repository: CompositeRepository) -> None:
        self.repository = repository

    async def attach(self, request: NotebookTagPath) -> CrudItemResponse:
        payload = request.model_dump(mode="json")
        data = await self.repository.create(RepositoryCreateItemRequest(payload=payload))
        return CrudItemResponse(data=data)

    async def detach(self, request: NotebookTagPath) -> CrudItemResponse:
        data = await self.repository.delete_by_filter(
            RepositoryFilterRequest(filters=request.model_dump(mode="json"))
        )
        if data is None:
            raise ResourceNotFoundError()
        return CrudItemResponse(data=data)
