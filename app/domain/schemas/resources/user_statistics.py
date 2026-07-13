from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class UserStatisticsSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class UserStatisticsRequest(UserStatisticsSchema):
    period: Literal["week", "month", "all"] = "week"
    timezone: str = Field(default="UTC", min_length=1, max_length=64)


class StatisticsOverview(UserStatisticsSchema):
    average_score: float = 0
    completed_exams: int = 0
    total_exams: int = 0
    notebooks_dominated: int = 0
    total_notebooks: int = 0
    total_study_seconds: int = 0


class ReinforcementNotebook(UserStatisticsSchema):
    notebook_id: UUID
    name: str
    mastery_percent: float = 0
    flashcards_count: int = 0
    exams_count: int = 0


class LearningPoint(UserStatisticsSchema):
    date: date
    exams_completed: int = 0
    flashcards_reviewed: int = 0
    study_minutes: int = 0


class UpcomingNotebook(UserStatisticsSchema):
    notebook_id: UUID
    name: str
    due_date: datetime


class StreakDay(UserStatisticsSchema):
    date: date
    active: bool


class StreakStatistics(UserStatisticsSchema):
    current_days: int = 0
    best_days: int = 0
    days: list[StreakDay] = Field(default_factory=list)


class NotebookTime(UserStatisticsSchema):
    notebook_id: UUID
    name: str
    study_seconds: int = 0
    percentage: float = 0


class RecentActivity(UserStatisticsSchema):
    activity_type: str
    occurred_at: datetime
    notebook_id: UUID | None = None
    notebook_name: str | None = None
    description: str
    quantity: int = 1
    duration_seconds: int = 0


class UserStatisticsData(UserStatisticsSchema):
    overview: StatisticsOverview
    reinforcement: list[ReinforcementNotebook] = Field(default_factory=list)
    learning: list[LearningPoint] = Field(default_factory=list)
    upcoming: list[UpcomingNotebook] = Field(default_factory=list)
    streak: StreakStatistics
    time_by_notebook: list[NotebookTime] = Field(default_factory=list)
    recent_activity: list[RecentActivity] = Field(default_factory=list)
    generated_at: datetime


class UserStatisticsResponse(UserStatisticsSchema):
    data: UserStatisticsData


class LearningEventCreate(UserStatisticsSchema):
    notebook_id: UUID
    activity_type: Literal["study_session", "flashcard_reviewed"]
    quantity: int = Field(default=1, ge=1, le=50)
    duration_seconds: int = Field(default=0, ge=0, le=14_400)

    @model_validator(mode="after")
    def validate_activity_shape(self) -> "LearningEventCreate":
        if self.activity_type == "study_session":
            if self.quantity != 1:
                raise ValueError("Una sesion de estudio debe tener quantity=1.")
            if self.duration_seconds < 30:
                raise ValueError("Una sesion de estudio debe durar al menos 30 segundos.")
        elif self.duration_seconds > 3_600:
            raise ValueError(
                "Un lote de repaso de flashcards no puede superar 3600 segundos."
            )
        return self


class LearningEventRead(UserStatisticsSchema):
    event_id: UUID
    user_id: UUID
    notebook_id: UUID
    activity_type: str
    quantity: int
    duration_seconds: int
    occurred_at: datetime


class LearningEventResponse(UserStatisticsSchema):
    data: LearningEventRead
