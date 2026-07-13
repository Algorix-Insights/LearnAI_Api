from __future__ import annotations

import asyncio
from typing import Any
from uuid import UUID

from supabase import Client

from app.core.exceptions import RepositoryError
from app.domain.schemas.resources.user_statistics import LearningEventCreate
from app.infra.db.supabase import get_supabase_admin_client


class UserStatisticsRepository:
    def __init__(self, client: Client | None = None) -> None:
        self.client = client or get_supabase_admin_client()

    async def load_snapshot(self, user_id: UUID) -> dict[str, list[dict[str, Any]]]:
        return await asyncio.to_thread(self._load_snapshot, str(user_id))

    async def record_event(
        self, user_id: UUID, event: LearningEventCreate
    ) -> dict[str, Any]:
        payload = {
            "user_id": str(user_id),
            **event.model_dump(mode="json"),
        }
        try:
            response = await asyncio.to_thread(
                self.client.table("user_learning_events").insert(payload).execute
            )
        except Exception as exc:
            raise RepositoryError("registrar la actividad") from exc
        return (response.data or [{}])[0]

    def _load_snapshot(self, user_id: str) -> dict[str, list[dict[str, Any]]]:
        try:
            notebook_ids = self._notebook_ids_for_user(user_id)
            notebooks = self._select_for_ids(
                "notebooks",
                "notebook_id,name,due_date,status,is_dominated",
                "notebook_id",
                notebook_ids,
            )
            exams = self._select_for_ids(
                "exams",
                "exam_id,notebook_id,name,status",
                "notebook_id",
                notebook_ids,
            )
            exam_ids = [str(item["exam_id"]) for item in exams if item.get("exam_id")]
            attempts = self._select_for_ids(
                "attempts",
                "attempt_id,exam_id,score,status,completed_at,started_at,spent_time,created_at",
                "exam_id",
                exam_ids,
                extra_filter=("user_id", user_id),
            )
            flashcards = self._select_for_ids(
                "flashcards",
                "flashcard_id,notebook_id,spent_time,created_at",
                "notebook_id",
                notebook_ids,
            )
            events_response = (
                self.client.table("user_learning_events")
                .select(
                    "event_id,user_id,notebook_id,activity_type,quantity,"
                    "duration_seconds,metadata,occurred_at"
                )
                .eq("user_id", user_id)
                .order("occurred_at", desc=True)
                .range(0, 4999)
                .execute()
            )
        except Exception as exc:
            raise RepositoryError("consultar las estadisticas") from exc
        return {
            "notebooks": notebooks,
            "exams": exams,
            "attempts": attempts,
            "flashcards": flashcards,
            "events": events_response.data or [],
        }

    def _notebook_ids_for_user(self, user_id: str) -> list[str]:
        personal = (
            self.client.table("personal_notebooks")
            .select("notebook_id")
            .eq("user_id", user_id)
            .range(0, 4999)
            .execute()
        ).data or []
        ids = {str(item["notebook_id"]) for item in personal if item.get("notebook_id")}

        members = (
            self.client.table("study_members")
            .select("member_id")
            .eq("user_id", user_id)
            .range(0, 100)
            .execute()
        ).data or []
        member_ids = [str(item["member_id"]) for item in members if item.get("member_id")]
        if member_ids:
            memberships = (
                self.client.table("members_rooms")
                .select("room_id")
                .in_("member_id", member_ids)
                .range(0, 4999)
                .execute()
            ).data or []
            room_ids = [str(item["room_id"]) for item in memberships if item.get("room_id")]
            if room_ids:
                shared = (
                    self.client.table("room_notebooks")
                    .select("notebook_id")
                    .in_("room_id", room_ids)
                    .range(0, 4999)
                    .execute()
                ).data or []
                ids.update(
                    str(item["notebook_id"])
                    for item in shared
                    if item.get("notebook_id")
                )
        return sorted(ids)

    def _select_for_ids(
        self,
        table: str,
        columns: str,
        id_field: str,
        ids: list[str],
        *,
        extra_filter: tuple[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        if not ids:
            return []
        query = self.client.table(table).select(columns).in_(id_field, ids)
        if extra_filter:
            query = query.eq(*extra_filter)
        return query.range(0, 4999).execute().data or []
