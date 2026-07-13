from __future__ import annotations

from datetime import datetime
from typing import Any

from app.core.exceptions import ApiError, RepositoryError
from app.domain.schemas.resources.attempts import (
    AttemptRepositoryCreateRequest,
    AttemptRepositoryDeleteRequest,
    AttemptRepositoryGetRequest,
    AttemptRepositoryListRequest,
    AttemptRepositoryUpdateRequest,
)
from app.infra.repositories.base import BaseSupabaseRepository


class AttemptRepository(BaseSupabaseRepository):
    table_name = "attempts"
    id_field = "attempt_id"

    async def list(self, request: AttemptRepositoryListRequest) -> list[dict]:
        return await self._list(self.table_name, request.limit, request.offset)

    async def get(self, request: AttemptRepositoryGetRequest) -> dict | None:
        return await self._get(self.table_name, self.id_field, str(request.attempt_id))

    async def create(self, request: AttemptRepositoryCreateRequest) -> dict:
        payload = request.payload.model_dump(exclude_unset=True, mode="json")
        return await self._create(self.table_name, payload)

    async def update(self, request: AttemptRepositoryUpdateRequest) -> dict | None:
        payload = request.payload.model_dump(exclude_unset=True, mode="json")
        return await self._update(self.table_name, self.id_field, str(request.attempt_id), payload)

    async def delete(self, request: AttemptRepositoryDeleteRequest) -> dict | None:
        return await self._delete(self.table_name, self.id_field, str(request.attempt_id))

    async def get_exam(self, *, exam_id: str) -> dict[str, Any] | None:
        try:
            query = (
                self.client.table("exams")
                .select("exam_id,notebook_id,status")
                .eq("exam_id", exam_id)
                .limit(1)
            )
            response = await self._execute(query)
        except Exception as exc:
            raise RepositoryError("consultar el examen") from exc
        return self._first(response.data)

    async def has_notebook_access(self, *, notebook_id: str, user_id: str) -> bool:
        try:
            personal_query = (
                self.client.table("personal_notebooks")
                .select("notebook_id")
                .eq("notebook_id", notebook_id)
                .eq("user_id", user_id)
                .limit(1)
            )
            personal = await self._execute(personal_query)
            if personal.data:
                return True

            member_query = (
                self.client.table("study_members")
                .select("member_id")
                .eq("user_id", user_id)
                .limit(1)
            )
            member = await self._execute(member_query)
            member_row = self._first(member.data)
            if member_row is None:
                return False

            rooms_query = (
                self.client.table("room_notebooks")
                .select("room_id")
                .eq("notebook_id", notebook_id)
            )
            rooms = await self._execute(rooms_query)
            room_ids = [row["room_id"] for row in rooms.data or []]
            if not room_ids:
                return False

            membership_query = (
                self.client.table("members_rooms")
                .select("room_id")
                .eq("member_id", member_row["member_id"])
                .in_("room_id", room_ids)
                .limit(1)
            )
            membership = await self._execute(membership_query)
        except Exception as exc:
            raise RepositoryError("validar acceso al examen") from exc
        return bool(membership.data)

    async def list_exam_questions(self, *, exam_id: str) -> list[dict[str, Any]]:
        try:
            links_query = (
                self.client.table("exam_questions")
                .select("question_id,question_order,points")
                .eq("exam_id", exam_id)
                .order("question_order")
            )
            links_response = await self._execute(links_query)
            links = links_response.data or []
            if not links:
                return []

            question_ids = [row["question_id"] for row in links]
            questions_query = (
                self.client.table("questions")
                .select("question_id,type,statement,expected_answer")
                .in_("question_id", question_ids)
            )
            questions_response = await self._execute(questions_query)
            options_query = (
                self.client.table("questions_options")
                .select("option_id,question_id,option_text,is_correct,option_order")
                .in_("question_id", question_ids)
                .order("option_order")
            )
            options_response = await self._execute(options_query)
        except Exception as exc:
            raise RepositoryError("listar preguntas del examen") from exc

        questions_by_id = {
            str(row["question_id"]): row for row in questions_response.data or []
        }
        options_by_question: dict[str, list[dict[str, Any]]] = {}
        for option in options_response.data or []:
            options_by_question.setdefault(str(option["question_id"]), []).append(option)

        questions: list[dict[str, Any]] = []
        for link in links:
            question_id = str(link["question_id"])
            question = questions_by_id.get(question_id)
            if question is None:
                continue
            questions.append(
                {
                    **question,
                    "question_order": link["question_order"],
                    "points": link["points"],
                    "options": options_by_question.get(question_id, []),
                }
            )
        return questions

    async def get_active_attempt(
        self, *, exam_id: str, user_id: str
    ) -> dict[str, Any] | None:
        try:
            query = (
                self.client.table(self.table_name)
                .select("*")
                .eq("exam_id", exam_id)
                .eq("user_id", user_id)
                .eq("status", "in_progress")
                .order("started_at", desc=True)
                .limit(1)
            )
            response = await self._execute(query)
        except Exception as exc:
            raise RepositoryError("consultar el intento activo") from exc
        return self._first(response.data)

    async def create_workflow_attempt(
        self, *, exam_id: str, user_id: str, started_at: datetime
    ) -> dict[str, Any] | None:
        del started_at
        try:
            query = self.client.rpc(
                "start_exam_attempt",
                {
                    "p_exam_id": exam_id,
                    "p_user_id": user_id,
                },
            )
            response = await self._execute(query)
        except Exception as exc:
            if "attempt_limit_reached" in self._error_text(exc):
                raise ApiError(
                    409,
                    "Alcanzaste el máximo de 5 intentos para este examen.",
                ) from exc
            raise RepositoryError("iniciar el intento") from exc
        return self._first(response.data)

    async def get_attempt_for_user(
        self, *, attempt_id: str, user_id: str
    ) -> dict[str, Any] | None:
        try:
            query = (
                self.client.table(self.table_name)
                .select("*")
                .eq("attempt_id", attempt_id)
                .eq("user_id", user_id)
                .limit(1)
            )
            response = await self._execute(query)
        except Exception as exc:
            raise RepositoryError("consultar el intento") from exc
        return self._first(response.data)

    async def list_attempt_answers(self, *, attempt_id: str) -> list[dict[str, Any]]:
        try:
            query = (
                self.client.table("user_answers")
                .select("*")
                .eq("attempt_id", attempt_id)
                .order("created_at")
            )
            response = await self._execute(query)
        except Exception as exc:
            raise RepositoryError("listar respuestas del intento") from exc
        return response.data or []

    async def submit_workflow_answer(
        self,
        *,
        attempt_id: str,
        user_id: str,
        question_id: str,
        selected_option_id: str | None,
        answer_text: str | None,
    ) -> dict[str, Any] | None:
        try:
            query = self.client.rpc(
                "submit_exam_attempt_answer",
                {
                    "p_attempt_id": attempt_id,
                    "p_user_id": user_id,
                    "p_question_id": question_id,
                    "p_selected_option_id": selected_option_id,
                    "p_answer_text": answer_text,
                },
            )
            response = await self._execute(query)
        except Exception as exc:
            raise RepositoryError("guardar la respuesta") from exc
        return self._first(response.data)

    async def finalize_workflow_attempt(
        self,
        *,
        attempt_id: str,
        user_id: str,
        completed_at: datetime,
        spent_time: int,
        grades: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        try:
            query = self.client.rpc(
                "finalize_exam_attempt",
                {
                    "p_attempt_id": attempt_id,
                    "p_user_id": user_id,
                    "p_completed_at": completed_at.isoformat(),
                    "p_spent_time": spent_time,
                    "p_grades": grades,
                },
            )
            response = await self._execute(query)
        except Exception as exc:
            if "attempt_answers_changed" in self._error_text(exc):
                return None
            raise RepositoryError("finalizar el intento") from exc
        return self._first(response.data)

    def _error_text(self, exc: Exception) -> str:
        return " ".join(
            str(value)
            for value in (
                getattr(exc, "message", ""),
                getattr(exc, "code", ""),
                exc,
            )
            if value
        ).casefold()
