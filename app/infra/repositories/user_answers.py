from app.domain.schemas.resources.user_answers import (
    UserAnswerRepositoryCreateRequest,
    UserAnswerRepositoryDeleteRequest,
    UserAnswerRepositoryGetRequest,
    UserAnswerRepositoryListRequest,
    UserAnswerRepositoryUpdateRequest,
)
from app.infra.repositories.base import BaseSupabaseRepository


class UserAnswerRepository(BaseSupabaseRepository):
    table_name = "user_answers"
    id_field = "answer_id"

    async def list(self, request: UserAnswerRepositoryListRequest) -> list[dict]:
        return await self._list(self.table_name, request.limit, request.offset)

    async def get(self, request: UserAnswerRepositoryGetRequest) -> dict | None:
        return await self._get(self.table_name, self.id_field, str(request.answer_id))

    async def create(self, request: UserAnswerRepositoryCreateRequest) -> dict:
        payload = request.payload.model_dump(exclude_unset=True, mode="json")
        return await self._create(self.table_name, payload)

    async def update(self, request: UserAnswerRepositoryUpdateRequest) -> dict | None:
        payload = request.payload.model_dump(exclude_unset=True, mode="json")
        return await self._update(self.table_name, self.id_field, str(request.answer_id), payload)

    async def delete(self, request: UserAnswerRepositoryDeleteRequest) -> dict | None:
        return await self._delete(self.table_name, self.id_field, str(request.answer_id))
