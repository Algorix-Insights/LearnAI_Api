from app.domain.schemas.resources.question_options import (
    QuestionOptionRepositoryCreateRequest,
    QuestionOptionRepositoryDeleteRequest,
    QuestionOptionRepositoryGetRequest,
    QuestionOptionRepositoryListRequest,
    QuestionOptionRepositoryUpdateRequest,
)
from app.infra.repositories.base import BaseSupabaseRepository


class QuestionOptionRepository(BaseSupabaseRepository):
    table_name = "questions_options"
    id_field = "option_id"
    safe_columns = "option_id,question_id,option_text,option_order,created_at"

    async def list(self, request: QuestionOptionRepositoryListRequest) -> list[dict]:
        return await self._list(
            self.table_name,
            request.limit,
            request.offset,
            columns=self.safe_columns,
        )

    async def get(self, request: QuestionOptionRepositoryGetRequest) -> dict | None:
        return await self._get(
            self.table_name,
            self.id_field,
            str(request.option_id),
            columns=self.safe_columns,
        )

    async def create(self, request: QuestionOptionRepositoryCreateRequest) -> dict:
        payload = request.payload.model_dump(exclude_unset=True, mode="json")
        return await self._create(
            self.table_name,
            payload,
            columns=self.safe_columns,
        )

    async def update(self, request: QuestionOptionRepositoryUpdateRequest) -> dict | None:
        payload = request.payload.model_dump(exclude_unset=True, mode="json")
        return await self._update(
            self.table_name,
            self.id_field,
            str(request.option_id),
            payload,
            columns=self.safe_columns,
        )

    async def delete(self, request: QuestionOptionRepositoryDeleteRequest) -> dict | None:
        return await self._delete(
            self.table_name,
            self.id_field,
            str(request.option_id),
            columns=self.safe_columns,
        )
