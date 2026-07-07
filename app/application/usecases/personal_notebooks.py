from app.core.exceptions import ResourceNotFoundError
from app.domain.interfaces import PersonalNotebookRepository
from app.domain.schemas.crud import CrudItemResponse
from app.domain.schemas.resources.users import (
    PersonalNotebookPath,
    PersonalNotebookRepositoryCreateRequest,
    PersonalNotebookRepositoryDeleteRequest,
)


class PersonalNotebookUseCase:
    def __init__(self, repository: PersonalNotebookRepository) -> None:
        self.repository = repository

    async def add(self, request: PersonalNotebookPath) -> CrudItemResponse:
        data = await self.repository.create(
            PersonalNotebookRepositoryCreateRequest(
                user_id=request.user_id,
                notebook_id=request.notebook_id,
            )
        )
        return CrudItemResponse(data=data)

    async def remove(self, request: PersonalNotebookPath) -> CrudItemResponse:
        data = await self.repository.delete(
            PersonalNotebookRepositoryDeleteRequest(
                user_id=request.user_id,
                notebook_id=request.notebook_id,
            )
        )
        if data is None:
            raise ResourceNotFoundError()
        return CrudItemResponse(data=data)
