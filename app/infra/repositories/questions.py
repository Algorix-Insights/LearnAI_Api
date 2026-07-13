from app.domain.schemas.resources.questions import (
    QuestionRepositoryCreateRequest,
    QuestionRepositoryDeleteRequest,
    QuestionRepositoryGetRequest,
    QuestionRepositoryListRequest,
    QuestionRepositoryUpdateRequest,
)
from app.infra.repositories.base import BaseSupabaseRepository


class QuestionRepository(BaseSupabaseRepository):
    table_name = "questions"
    id_field = "question_id"
    safe_columns = "question_id,type,statement,created_at"

    async def list(self, request: QuestionRepositoryListRequest) -> list[dict]:
        return await self._list(
            self.table_name,
            request.limit,
            request.offset,
            columns=self.safe_columns,
        )

    async def get(self, request: QuestionRepositoryGetRequest) -> dict | None:
        return await self._get(
            self.table_name,
            self.id_field,
            str(request.question_id),
            columns=self.safe_columns,
        )

    async def create(self, request: QuestionRepositoryCreateRequest) -> dict:
        payload = request.payload.model_dump(exclude_unset=True, mode="json")
        return await self._create(
            self.table_name,
            payload,
            columns=self.safe_columns,
        )

    async def update(self, request: QuestionRepositoryUpdateRequest) -> dict | None:
        payload = request.payload.model_dump(exclude_unset=True, mode="json")
        return await self._update(
            self.table_name,
            self.id_field,
            str(request.question_id),
            payload,
            columns=self.safe_columns,
        )

    async def delete(self, request: QuestionRepositoryDeleteRequest) -> dict | None:
        return await self._delete(
            self.table_name,
            self.id_field,
            str(request.question_id),
            columns=self.safe_columns,
        )
