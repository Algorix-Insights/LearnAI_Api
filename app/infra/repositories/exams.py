from app.domain.schemas.resources.exams import (
    ExamQuestionRepositoryCreateRequest,
    ExamQuestionRepositoryDeleteRequest,
    ExamRepositoryCreateRequest,
    ExamRepositoryDeleteRequest,
    ExamRepositoryGetRequest,
    ExamRepositoryListRequest,
    ExamRepositoryUpdateRequest,
)
from app.infra.repositories.base import BaseSupabaseRepository


class ExamRepository(BaseSupabaseRepository):
    table_name = "exams"
    id_field = "exam_id"

    async def list(self, request: ExamRepositoryListRequest) -> list[dict]:
        return await self._list(self.table_name, request.limit, request.offset)

    async def get(self, request: ExamRepositoryGetRequest) -> dict | None:
        return await self._get(self.table_name, self.id_field, str(request.exam_id))

    async def create(self, request: ExamRepositoryCreateRequest) -> dict:
        payload = request.payload.model_dump(exclude_unset=True, mode="json")
        return await self._create(self.table_name, payload)

    async def update(self, request: ExamRepositoryUpdateRequest) -> dict | None:
        payload = request.payload.model_dump(exclude_unset=True, mode="json")
        payload["updated_at"] = request.updated_at.isoformat()
        return await self._update(self.table_name, self.id_field, str(request.exam_id), payload)

    async def delete(self, request: ExamRepositoryDeleteRequest) -> dict | None:
        return await self._delete(self.table_name, self.id_field, str(request.exam_id))


class ExamQuestionRepository(BaseSupabaseRepository):
    table_name = "exam_questions"

    async def create(self, request: ExamQuestionRepositoryCreateRequest) -> dict:
        return await self._create(self.table_name, request.model_dump(mode="json"))

    async def delete(self, request: ExamQuestionRepositoryDeleteRequest) -> dict | None:
        return await self._delete_by_filter(self.table_name, request.model_dump(mode="json"))
