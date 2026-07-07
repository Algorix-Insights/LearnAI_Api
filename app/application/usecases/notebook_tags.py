from app.core.exceptions import ResourceNotFoundError
from app.domain.interfaces import NotebookTagRepository
from app.domain.schemas.crud import CrudItemResponse
from app.domain.schemas.resources.notebooks import (
    NotebookTagPath,
    NotebookTagRepositoryCreateRequest,
    NotebookTagRepositoryDeleteRequest,
)


class NotebookTagUseCase:
    def __init__(self, repository: NotebookTagRepository) -> None:
        self.repository = repository

    async def attach(self, request: NotebookTagPath) -> CrudItemResponse:
        data = await self.repository.create(
            NotebookTagRepositoryCreateRequest(
                notebook_id=request.notebook_id,
                tag_id=request.tag_id,
            )
        )
        return CrudItemResponse(data=data)

    async def detach(self, request: NotebookTagPath) -> CrudItemResponse:
        data = await self.repository.delete(
            NotebookTagRepositoryDeleteRequest(
                notebook_id=request.notebook_id,
                tag_id=request.tag_id,
            )
        )
        if data is None:
            raise ResourceNotFoundError()
        return CrudItemResponse(data=data)
