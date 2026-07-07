from app.domain.schemas.resources.study_members import (
    StudyMemberRepositoryCreateRequest,
    StudyMemberRepositoryDeleteRequest,
    StudyMemberRepositoryGetRequest,
    StudyMemberRepositoryListRequest,
    StudyMemberRepositoryUpdateRequest,
)
from app.infra.repositories.base import BaseSupabaseRepository


class StudyMemberRepository(BaseSupabaseRepository):
    table_name = "study_members"
    id_field = "member_id"

    async def list(self, request: StudyMemberRepositoryListRequest) -> list[dict]:
        return await self._list(self.table_name, request.limit, request.offset)

    async def get(self, request: StudyMemberRepositoryGetRequest) -> dict | None:
        return await self._get(self.table_name, self.id_field, str(request.member_id))

    async def create(self, request: StudyMemberRepositoryCreateRequest) -> dict:
        payload = request.payload.model_dump(exclude_unset=True, mode="json")
        return await self._create(self.table_name, payload)

    async def update(self, request: StudyMemberRepositoryUpdateRequest) -> dict | None:
        payload = request.payload.model_dump(exclude_unset=True, mode="json")
        payload["updated_at"] = request.updated_at.isoformat()
        return await self._update(self.table_name, self.id_field, str(request.member_id), payload)

    async def delete(self, request: StudyMemberRepositoryDeleteRequest) -> dict | None:
        return await self._delete(self.table_name, self.id_field, str(request.member_id))
