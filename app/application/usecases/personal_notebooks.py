from app.core.exceptions import ResourceNotFoundError
from app.domain.interfaces import CompositeRepository
from app.domain.schemas import PersonalNotebookPath
from app.domain.schemas.aggregate import RepositoryCreateItemRequest, RepositoryFilterRequest
from app.domain.schemas.crud import CrudItemResponse


class PersonalNotebookUseCase:
    def __init__(self, repository: CompositeRepository) -> None:
        self.repository = repository

    async def add(self, request: PersonalNotebookPath) -> CrudItemResponse:
        payload = request.model_dump(mode="json")
        data = await self.repository.create(RepositoryCreateItemRequest(payload=payload))
        return CrudItemResponse(data=data)

    async def remove(self, request: PersonalNotebookPath) -> CrudItemResponse:
        filters = request.model_dump(mode="json")
        data = await self.repository.delete_by_filter(RepositoryFilterRequest(filters=filters))
        if data is None:
            raise ResourceNotFoundError()
        return CrudItemResponse(data=data)
