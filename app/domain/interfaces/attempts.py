from datetime import datetime
from typing import Any, Protocol

from app.domain.schemas.resources.attempts import (
    AttemptRepositoryCreateRequest,
    AttemptRepositoryDeleteRequest,
    AttemptRepositoryGetRequest,
    AttemptRepositoryListRequest,
    AttemptRepositoryUpdateRequest,
)


class AttemptRepository(Protocol):
    async def list(self, request: AttemptRepositoryListRequest) -> list[dict]:
        raise NotImplementedError

    async def get(self, request: AttemptRepositoryGetRequest) -> dict | None:
        raise NotImplementedError

    async def create(self, request: AttemptRepositoryCreateRequest) -> dict:
        raise NotImplementedError

    async def update(self, request: AttemptRepositoryUpdateRequest) -> dict | None:
        raise NotImplementedError

    async def delete(self, request: AttemptRepositoryDeleteRequest) -> dict | None:
        raise NotImplementedError


class ExamAttemptWorkflowRepository(Protocol):
    async def get_exam(self, *, exam_id: str) -> dict[str, Any] | None:
        raise NotImplementedError

    async def has_notebook_access(self, *, notebook_id: str, user_id: str) -> bool:
        raise NotImplementedError

    async def list_exam_questions(self, *, exam_id: str) -> list[dict[str, Any]]:
        raise NotImplementedError

    async def get_active_attempt(
        self, *, exam_id: str, user_id: str
    ) -> dict[str, Any] | None:
        raise NotImplementedError

    async def create_workflow_attempt(
        self, *, exam_id: str, user_id: str, started_at: datetime
    ) -> dict[str, Any] | None:
        raise NotImplementedError

    async def get_attempt_for_user(
        self, *, attempt_id: str, user_id: str
    ) -> dict[str, Any] | None:
        raise NotImplementedError

    async def list_attempt_answers(self, *, attempt_id: str) -> list[dict[str, Any]]:
        raise NotImplementedError

    async def submit_workflow_answer(
        self,
        *,
        attempt_id: str,
        user_id: str,
        question_id: str,
        selected_option_id: str | None,
        answer_text: str | None,
    ) -> dict[str, Any] | None:
        raise NotImplementedError

    async def finalize_workflow_attempt(
        self,
        *,
        attempt_id: str,
        user_id: str,
        completed_at: datetime,
        spent_time: int,
        grades: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        raise NotImplementedError
