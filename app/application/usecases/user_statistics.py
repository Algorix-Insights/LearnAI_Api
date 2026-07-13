from __future__ import annotations

import re
from collections import Counter, defaultdict
from datetime import UTC, date, datetime, timedelta
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.core.exceptions import BadRequestError
from app.domain.interfaces.user_statistics import UserStatisticsRepository
from app.domain.schemas.resources.user_statistics import (
    LearningEventCreate,
    LearningEventResponse,
    LearningPoint,
    NotebookTime,
    RecentActivity,
    ReinforcementNotebook,
    StatisticsOverview,
    StreakDay,
    StreakStatistics,
    UpcomingNotebook,
    UserStatisticsData,
    UserStatisticsRequest,
    UserStatisticsResponse,
)


class UserStatisticsUseCase:
    _IDEMPOTENCY_KEY_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{15,127}$")

    def __init__(self, repository: UserStatisticsRepository) -> None:
        self.repository = repository

    async def get(
        self, user_id: UUID, request: UserStatisticsRequest
    ) -> UserStatisticsResponse:
        timezone = self._timezone(request.timezone)
        now = datetime.now(UTC)
        snapshot = await self.repository.load_snapshot(user_id)
        data = self._build(snapshot, request=request, timezone=timezone, now=now)
        return UserStatisticsResponse(data=data)

    async def record(
        self,
        user_id: UUID,
        event: LearningEventCreate,
        idempotency_key: str,
    ) -> LearningEventResponse:
        if not self._IDEMPOTENCY_KEY_PATTERN.fullmatch(idempotency_key):
            raise BadRequestError("Idempotency-Key invalido.")
        # Ownership, quotas and uniqueness are checked atomically in PostgreSQL.
        # Doing a read here first would leave a time-of-check/time-of-use race.
        data = await self.repository.record_event(user_id, event, idempotency_key)
        return LearningEventResponse(data=data)

    def _build(
        self,
        snapshot: dict[str, list[dict[str, Any]]],
        *,
        request: UserStatisticsRequest,
        timezone: ZoneInfo,
        now: datetime,
    ) -> UserStatisticsData:
        notebooks = snapshot.get("notebooks", [])
        exams = snapshot.get("exams", [])
        attempts = snapshot.get("attempts", [])
        flashcards = snapshot.get("flashcards", [])
        events = snapshot.get("events", [])
        notebook_by_id = {
            str(item["notebook_id"]): item for item in notebooks if item.get("notebook_id")
        }
        exam_by_id = {str(item["exam_id"]): item for item in exams if item.get("exam_id")}

        completed = [item for item in attempts if item.get("status") == "completed"]
        scores = [self._score(item.get("score")) for item in completed]
        scores_by_notebook: dict[str, list[float]] = defaultdict(list)
        exam_count_by_notebook: Counter[str] = Counter()
        flashcard_count_by_notebook: Counter[str] = Counter()
        study_seconds_by_notebook: Counter[str] = Counter()
        active_dates: set[date] = set()
        recent: list[RecentActivity] = []

        for exam in exams:
            if exam.get("status") == "active" and exam.get("notebook_id"):
                exam_count_by_notebook[str(exam["notebook_id"])] += 1
        for flashcard in flashcards:
            if flashcard.get("notebook_id"):
                flashcard_count_by_notebook[str(flashcard["notebook_id"])] += 1

        for attempt in completed:
            exam = exam_by_id.get(str(attempt.get("exam_id")))
            notebook_id = str(exam.get("notebook_id")) if exam else ""
            if notebook_id:
                scores_by_notebook[notebook_id].append(self._score(attempt.get("score")))
                study_seconds_by_notebook[notebook_id] += max(
                    0, int(attempt.get("spent_time") or 0)
                )
            occurred_at = self._datetime(
                attempt.get("completed_at") or attempt.get("created_at")
            )
            if occurred_at:
                active_dates.add(occurred_at.astimezone(timezone).date())
                recent.append(
                    RecentActivity(
                        activity_type="exam_completed",
                        occurred_at=occurred_at,
                        notebook_id=notebook_id or None,
                        notebook_name=self._notebook_name(notebook_by_id, notebook_id),
                        description=f"Completaste el examen {exam.get('name') or ''}".strip()
                        if exam
                        else "Completaste un examen",
                        duration_seconds=max(0, int(attempt.get("spent_time") or 0)),
                    )
                )

        for event in events:
            occurred_at = self._datetime(event.get("occurred_at"))
            if not occurred_at:
                continue
            notebook_id = str(event.get("notebook_id") or "")
            active_dates.add(occurred_at.astimezone(timezone).date())
            duration = max(0, int(event.get("duration_seconds") or 0))
            quantity = max(1, int(event.get("quantity") or 1))
            if notebook_id:
                study_seconds_by_notebook[notebook_id] += duration
            activity_type = str(event.get("activity_type") or "activity")
            recent.append(
                RecentActivity(
                    activity_type=activity_type,
                    occurred_at=occurred_at,
                    notebook_id=notebook_id or None,
                    notebook_name=self._notebook_name(notebook_by_id, notebook_id),
                    description=self._event_description(activity_type, quantity),
                    quantity=quantity,
                    duration_seconds=duration,
                )
            )

        mastery = {
            notebook_id: round(sum(values) / len(values), 2) if values else 0
            for notebook_id, values in scores_by_notebook.items()
        }
        dominated = sum(
            1
            for notebook_id in notebook_by_id
            if mastery.get(notebook_id, 0) >= 80
        )
        reinforcement = sorted(
            [
                ReinforcementNotebook(
                    notebook_id=UUID(notebook_id),
                    name=str(notebook.get("name") or "Cuaderno"),
                    mastery_percent=mastery.get(notebook_id, 0),
                    flashcards_count=flashcard_count_by_notebook[notebook_id],
                    exams_count=exam_count_by_notebook[notebook_id],
                )
                for notebook_id, notebook in notebook_by_id.items()
                if mastery.get(notebook_id, 0) < 70
            ],
            key=lambda item: (item.mastery_percent, item.name),
        )[:5]

        local_now = now.astimezone(timezone)
        period_start = self._period_start(local_now.date(), request.period)
        learning = self._learning_points(
            completed,
            events,
            exam_by_id,
            timezone,
            period_start,
            local_now.date(),
        )
        upcoming = self._upcoming(notebook_by_id, now)
        streak = self._streak(active_dates, local_now.date())
        time_by_notebook = self._time_by_notebook(
            notebook_by_id, study_seconds_by_notebook
        )

        return UserStatisticsData(
            overview=StatisticsOverview(
                average_score=round(sum(scores) / len(scores), 2) if scores else 0,
                completed_exams=len(completed),
                total_exams=len(exams),
                notebooks_dominated=dominated,
                total_notebooks=len(notebooks),
                total_study_seconds=sum(study_seconds_by_notebook.values()),
            ),
            reinforcement=reinforcement,
            learning=learning,
            upcoming=upcoming,
            streak=streak,
            time_by_notebook=time_by_notebook,
            recent_activity=sorted(
                recent, key=lambda item: item.occurred_at, reverse=True
            )[:10],
            generated_at=now,
        )

    def _learning_points(
        self,
        attempts: list[dict[str, Any]],
        events: list[dict[str, Any]],
        exam_by_id: dict[str, dict[str, Any]],
        timezone: ZoneInfo,
        start: date,
        end: date,
    ) -> list[LearningPoint]:
        values: dict[date, dict[str, int]] = defaultdict(
            lambda: {"exams": 0, "flashcards": 0, "seconds": 0}
        )
        for attempt in attempts:
            occurred = self._datetime(attempt.get("completed_at") or attempt.get("created_at"))
            if not occurred:
                continue
            day = occurred.astimezone(timezone).date()
            if start <= day <= end:
                values[day]["exams"] += 1
                values[day]["seconds"] += max(0, int(attempt.get("spent_time") or 0))
        for event in events:
            occurred = self._datetime(event.get("occurred_at"))
            if not occurred:
                continue
            day = occurred.astimezone(timezone).date()
            if not start <= day <= end:
                continue
            if event.get("activity_type") == "flashcard_reviewed":
                values[day]["flashcards"] += max(1, int(event.get("quantity") or 1))
            values[day]["seconds"] += max(0, int(event.get("duration_seconds") or 0))
        points: list[LearningPoint] = []
        cursor = start
        while cursor <= end:
            item = values[cursor]
            points.append(
                LearningPoint(
                    date=cursor,
                    exams_completed=item["exams"],
                    flashcards_reviewed=item["flashcards"],
                    study_minutes=round(item["seconds"] / 60),
                )
            )
            cursor += timedelta(days=1)
        return points

    def _upcoming(
        self, notebook_by_id: dict[str, dict[str, Any]], now: datetime
    ) -> list[UpcomingNotebook]:
        items: list[UpcomingNotebook] = []
        for notebook_id, notebook in notebook_by_id.items():
            due = self._datetime(notebook.get("due_date"))
            if due and due >= now and notebook.get("status") != "deleted":
                items.append(
                    UpcomingNotebook(
                        notebook_id=UUID(notebook_id),
                        name=str(notebook.get("name") or "Cuaderno"),
                        due_date=due,
                    )
                )
        return sorted(items, key=lambda item: item.due_date)[:5]

    def _streak(self, active_dates: set[date], today: date) -> StreakStatistics:
        best = current_run = 0
        previous: date | None = None
        for day in sorted(active_dates):
            current_run = current_run + 1 if previous and day == previous + timedelta(days=1) else 1
            best = max(best, current_run)
            previous = day
        anchor = today if today in active_dates else today - timedelta(days=1)
        current = 0
        while anchor in active_dates:
            current += 1
            anchor -= timedelta(days=1)
        days = [
            StreakDay(date=today - timedelta(days=offset), active=today - timedelta(days=offset) in active_dates)
            for offset in reversed(range(7))
        ]
        return StreakStatistics(current_days=current, best_days=best, days=days)

    def _time_by_notebook(
        self,
        notebook_by_id: dict[str, dict[str, Any]],
        seconds_by_notebook: Counter[str],
    ) -> list[NotebookTime]:
        total = sum(seconds_by_notebook.values())
        items = [
            NotebookTime(
                notebook_id=UUID(notebook_id),
                name=self._notebook_name(notebook_by_id, notebook_id) or "Cuaderno",
                study_seconds=seconds,
                percentage=round(seconds * 100 / total, 2) if total else 0,
            )
            for notebook_id, seconds in seconds_by_notebook.items()
            if notebook_id in notebook_by_id and seconds > 0
        ]
        return sorted(items, key=lambda item: item.study_seconds, reverse=True)

    def _period_start(self, today: date, period: str) -> date:
        if period == "week":
            return today - timedelta(days=today.weekday())
        if period == "month":
            return today.replace(day=1)
        return today - timedelta(days=364)

    def _timezone(self, name: str) -> ZoneInfo:
        try:
            return ZoneInfo(name)
        except ZoneInfoNotFoundError as exc:
            raise BadRequestError("Zona horaria invalida.") from exc

    def _score(self, value: Any) -> float:
        try:
            return min(100.0, max(0.0, float(value or 0)))
        except (TypeError, ValueError):
            return 0

    def _datetime(self, value: Any) -> datetime | None:
        if isinstance(value, datetime):
            result = value
        elif isinstance(value, str):
            try:
                result = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        else:
            return None
        return result.replace(tzinfo=UTC) if result.tzinfo is None else result.astimezone(UTC)

    def _notebook_name(
        self, notebook_by_id: dict[str, dict[str, Any]], notebook_id: str
    ) -> str | None:
        notebook = notebook_by_id.get(notebook_id)
        return str(notebook.get("name")) if notebook and notebook.get("name") else None

    def _event_description(self, activity_type: str, quantity: int) -> str:
        if activity_type == "flashcard_reviewed":
            return f"Repasaste {quantity} flashcards"
        if activity_type == "study_session":
            return "Completaste una sesion de estudio"
        if activity_type == "resource_generated":
            return f"Generaste {quantity} recurso(s) de estudio"
        if activity_type == "document_uploaded":
            return "Subiste un documento"
        if activity_type == "notebook_shared":
            return "Compartiste un cuaderno"
        return "Registraste actividad de aprendizaje"
