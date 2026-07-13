from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class HealthCreate(StrictSchema):
    status: str


class HealthUpdate(StrictSchema):
    status: str | None = None


class UserCreate(StrictSchema):
    user_id: UUID | None = None
    name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=320)
    streak: int = Field(default=0, ge=0)
    status: Literal["active", "inactive", "suspended"] = "active"
    last_login: datetime | None = None
    profile_image_path: str | None = None
    profile_image_mime_type: str | None = None
    profile_image_size_bytes: int | None = Field(default=None, ge=0)


class UserUpdate(StrictSchema):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    email: str | None = Field(default=None, min_length=3, max_length=320)
    streak: int | None = Field(default=None, ge=0)
    status: Literal["active", "inactive", "suspended"] | None = None
    last_login: datetime | None = None
    profile_image_path: str | None = None
    profile_image_mime_type: str | None = None
    profile_image_size_bytes: int | None = Field(default=None, ge=0)


class NotebookCreate(StrictSchema):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    summary: str | None = Field(default=None, max_length=10000)
    is_favorite: bool = False
    due_date: datetime | None = None


class NotebookUpdate(StrictSchema):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    summary: str | None = Field(default=None, max_length=10000)
    is_favorite: bool | None = None
    status: Literal["active", "archived", "deleted"] | None = None
    due_date: datetime | None = None


class RoomCreate(StrictSchema):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)


class RoomUpdate(StrictSchema):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)


class StudyMemberCreate(StrictSchema):
    user_id: UUID
    nickname: str


class StudyMemberUpdate(StrictSchema):
    nickname: str | None = None


class MemberRoomCreate(StrictSchema):
    member_id: UUID
    room_id: UUID
    role: Literal["user", "admin"] = "user"


class MemberRoomUpdate(StrictSchema):
    role: Literal["user", "admin"] | None = None


class PersonalNotebookCreate(StrictSchema):
    notebook_id: UUID
    user_id: UUID


class PersonalNotebookUpdate(StrictSchema):
    user_id: UUID | None = None


class RoomNotebookCreate(StrictSchema):
    notebook_id: UUID
    room_id: UUID
    created_by: UUID


class RoomNotebookUpdate(StrictSchema):
    room_id: UUID | None = None
    created_by: UUID | None = None


class ExamCreate(StrictSchema):
    notebook_id: UUID
    name: str
    description: str | None = None
    status: Literal["active", "archived", "deleted"] = "active"


class ExamUpdate(StrictSchema):
    name: str | None = None
    description: str | None = None
    status: Literal["active", "archived", "deleted"] | None = None


class QuestionCreate(StrictSchema):
    type: Literal["multiple_choice", "true_false", "open"] = "multiple_choice"
    statement: str
    expected_answer: str | None = None

    @model_validator(mode="after")
    def validate_expected_answer(self) -> "QuestionCreate":
        if self.type == "open" and self.expected_answer is None:
            raise ValueError("La respuesta esperada es obligatoria para preguntas abiertas.")
        if self.type in {"multiple_choice", "true_false"} and self.expected_answer is not None:
            raise ValueError("La respuesta esperada solo aplica para preguntas abiertas.")
        return self


class QuestionUpdate(StrictSchema):
    type: Literal["multiple_choice", "true_false", "open"] | None = None
    statement: str | None = None
    expected_answer: str | None = None


class ExamQuestionCreate(StrictSchema):
    exam_id: UUID
    question_id: UUID
    question_order: int = Field(gt=0)
    points: Decimal = Field(default=Decimal("1"), ge=0)


class ExamQuestionUpdate(StrictSchema):
    question_order: int | None = Field(default=None, gt=0)
    points: Decimal | None = Field(default=None, ge=0)


class QuestionOptionCreate(StrictSchema):
    question_id: UUID
    option_text: str
    is_correct: bool = False
    option_order: int = Field(gt=0)


class QuestionOptionUpdate(StrictSchema):
    option_text: str | None = None
    is_correct: bool | None = None
    option_order: int | None = Field(default=None, gt=0)


class AttemptCreate(StrictSchema):
    exam_id: UUID
    user_id: UUID
    score: Decimal = Field(default=Decimal("0"), ge=0)
    status: Literal["in_progress", "completed", "failed", "not_started"] = "in_progress"
    completed_at: datetime | None = None
    started_at: datetime | None = None
    spent_time: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def validate_dates(self) -> "AttemptCreate":
        if self.completed_at and self.started_at and self.completed_at < self.started_at:
            raise ValueError("La fecha de finalizacion no puede ser menor a la fecha de inicio.")
        return self


class AttemptUpdate(StrictSchema):
    exam_id: UUID | None = None
    user_id: UUID | None = None
    score: Decimal | None = Field(default=None, ge=0)
    status: Literal["in_progress", "completed", "failed", "not_started"] | None = None
    completed_at: datetime | None = None
    started_at: datetime | None = None
    spent_time: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_dates(self) -> "AttemptUpdate":
        if self.completed_at and self.started_at and self.completed_at < self.started_at:
            raise ValueError("La fecha de finalizacion no puede ser menor a la fecha de inicio.")
        return self


class UserAnswerCreate(StrictSchema):
    attempt_id: UUID
    question_id: UUID
    selected_option_id: UUID | None = None
    answer_text: str | None = None
    is_correct: bool | None = None
    points_awarded: Decimal = Field(default=Decimal("0"), ge=0)

    @model_validator(mode="after")
    def validate_answer_value(self) -> "UserAnswerCreate":
        has_selected_option = self.selected_option_id is not None
        has_answer_text = self.answer_text is not None
        if has_selected_option == has_answer_text:
            raise ValueError("Debe enviar una opcion seleccionada o una respuesta de texto, no ambas.")
        return self


class UserAnswerUpdate(StrictSchema):
    selected_option_id: UUID | None = None
    answer_text: str | None = None
    is_correct: bool | None = None
    points_awarded: Decimal | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_answer_value(self) -> "UserAnswerUpdate":
        has_selected_option = self.selected_option_id is not None
        has_answer_text = self.answer_text is not None
        if has_selected_option and has_answer_text:
            raise ValueError("Debe enviar una opcion seleccionada o una respuesta de texto, no ambas.")
        return self


class FlashcardCreate(StrictSchema):
    notebook_id: UUID
    question_id: UUID
    spent_time: int = Field(default=0, ge=0)


class FlashcardUpdate(StrictSchema):
    notebook_id: UUID | None = None
    question_id: UUID | None = None
    spent_time: int | None = Field(default=None, ge=0)


class DocumentCreate(StrictSchema):
    notebook_id: UUID
    name: str
    description: str | None = None
    source_type: Literal["note", "pdf", "markdown", "txt", "document"]
    storage_path: str | None = None
    status: Literal["active", "archived", "deleted"] = "active"
    processing_status: Literal["pending", "processing", "completed", "failed"] = "pending"
    mime_type: str | None = None
    content_text: str | None = None
    content_hash: str
    size_bytes: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def validate_source(self) -> "DocumentCreate":
        if self.source_type == "note" and self.content_text is None:
            raise ValueError("El contenido es obligatorio cuando el origen es nota.")
        if self.source_type != "note" and self.storage_path is None:
            raise ValueError("La ruta de almacenamiento es obligatoria para este origen.")
        return self


class DocumentUpdate(StrictSchema):
    notebook_id: UUID | None = None
    name: str | None = None
    description: str | None = None
    source_type: Literal["note", "pdf", "markdown", "txt", "document"] | None = None
    storage_path: str | None = None
    status: Literal["active", "archived", "deleted"] | None = None
    processing_status: Literal["pending", "processing", "completed", "failed"] | None = None
    mime_type: str | None = None
    content_text: str | None = None
    content_hash: str | None = None
    size_bytes: int | None = Field(default=None, ge=0)


class DocumentChunkCreate(StrictSchema):
    document_id: UUID
    chunk_index: int = Field(ge=0)
    content: str
    embedding: list[float]
    model: str
    token_count: int | None = Field(default=None, ge=0)


class DocumentChunkUpdate(StrictSchema):
    document_id: UUID | None = None
    chunk_index: int | None = Field(default=None, ge=0)
    content: str | None = None
    embedding: list[float] | None = None
    model: str | None = None
    token_count: int | None = Field(default=None, ge=0)


class TagCreate(StrictSchema):
    name: str = Field(max_length=100)
    status: Literal["active", "inactive"] = "active"


class TagUpdate(StrictSchema):
    name: str | None = Field(default=None, max_length=100)
    status: Literal["active", "inactive"] | None = None


class NotebookTagCreate(StrictSchema):
    notebook_id: UUID
    tag_id: UUID


class NotebookTagUpdate(StrictSchema):
    notebook_id: UUID | None = None
    tag_id: UUID | None = None
