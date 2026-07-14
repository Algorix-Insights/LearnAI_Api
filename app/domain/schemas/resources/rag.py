from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class RagSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DocumentUploadResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    document_id: UUID | None = None
    notebook_id: UUID | None = None
    name: str | None = None
    source_type: str | None = None
    processing_status: str | None = None
    mime_type: str | None = None
    size_bytes: int | None = None
    chunks_count: int = 0


class DocumentUploadResponse(RagSchema):
    data: DocumentUploadResult


class ProfilePhotoResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: UUID | None = None
    profile_image_path: str | None = None
    profile_image_mime_type: str | None = None
    profile_image_size_bytes: int | None = None


class ProfilePhotoResponse(RagSchema):
    data: ProfilePhotoResult


class ConversationCreateRequest(RagSchema):
    name: str = Field(default="Nueva conversacion", min_length=1, max_length=120)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("El nombre no puede estar vacio.")
        return value


class ConversationRead(BaseModel):
    model_config = ConfigDict(extra="allow")

    conversation_id: UUID | None = None
    notebook_id: UUID | None = None
    created_by_user_id: UUID | None = None
    name: str | None = None
    summary: str | None = None
    spent_time: int | None = None
    status: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ConversationResponse(RagSchema):
    data: ConversationRead


class ConversationListResponse(RagSchema):
    data: list[ConversationRead]
    limit: int
    offset: int


class MessageRead(BaseModel):
    model_config = ConfigDict(extra="allow")

    message_id: UUID | None = None
    conversation_id: UUID | None = None
    sent_by_user_id: UUID | None = None
    role: str | None = None
    content: str | None = None
    order_message: int | None = None
    created_at: datetime | None = None


class MessageListResponse(RagSchema):
    data: list[MessageRead]
    limit: int
    offset: int


class ChatRequest(RagSchema):
    content: str = Field(min_length=1, max_length=4000)
    model: str | None = Field(
        default=None,
        min_length=1,
        max_length=120,
        pattern=r"^[A-Za-z0-9._:/-]+$",
    )

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("El contenido no puede estar vacio.")
        return value


class RagSource(BaseModel):
    model_config = ConfigDict(extra="allow")

    chunk_id: UUID | None = None
    document_id: UUID | None = None
    document_name: str | None = None
    similarity: float | None = None
    content: str | None = None


class ChatResponse(RagSchema):
    data: MessageRead
    sources: list[RagSource]


class FlashcardGenerationRequest(RagSchema):
    count: int = Field(default=10, ge=1, le=20)
    model: str | None = Field(
        default=None,
        min_length=1,
        max_length=120,
        pattern=r"^[A-Za-z0-9._:/-]+$",
    )


class FlashcardDraft(RagSchema):
    question: str = Field(min_length=1, max_length=1000)
    answer: str = Field(min_length=1, max_length=2000)

    @model_validator(mode="after")
    def validate_text(self) -> "FlashcardDraft":
        self.question = self.question.strip()
        self.answer = self.answer.strip()
        if not self.question or not self.answer:
            raise ValueError("Pregunta y respuesta no pueden estar vacias.")
        return self


class FlashcardDraftSet(RagSchema):
    flashcards: list[FlashcardDraft] = Field(min_length=1, max_length=20)

    @model_validator(mode="after")
    def validate_unique_questions(self) -> "FlashcardDraftSet":
        normalized = [item.question.strip().casefold() for item in self.flashcards]
        if len(normalized) != len(set(normalized)):
            raise ValueError("Las preguntas de las flashcards deben ser unicas.")
        return self


class GeneratedFlashcardRead(RagSchema):
    flashcard_id: UUID
    question_id: UUID
    question: str
    answer: str


class FlashcardGenerationResponse(RagSchema):
    data: list[GeneratedFlashcardRead]
    sources: list[RagSource]


class FlashcardStudyRead(RagSchema):
    flashcard_id: UUID
    question_id: UUID
    notebook_id: UUID
    question: str
    answer: str
    spent_time: int = 0
    created_at: datetime | None = None


class FlashcardStudyListResponse(RagSchema):
    data: list[FlashcardStudyRead]
    limit: int
    offset: int


class MultipleChoiceQuestionDraft(RagSchema):
    type: Literal["multiple_choice"]
    statement: str = Field(min_length=1, max_length=2000)
    options: list[str] = Field(min_length=2, max_length=6)
    correct_option_index: int = Field(ge=0, le=5)

    @model_validator(mode="after")
    def validate_options(self) -> "MultipleChoiceQuestionDraft":
        self.statement = self.statement.strip()
        if not self.statement:
            raise ValueError("El enunciado no puede estar vacio.")
        options = [option.strip() for option in self.options]
        if any(not option or len(option) > 1000 for option in options):
            raise ValueError("Cada opcion debe tener entre 1 y 1000 caracteres.")
        if len({option.casefold() for option in options}) != len(options):
            raise ValueError("Las opciones deben ser unicas.")
        if self.correct_option_index >= len(options):
            raise ValueError("El indice de respuesta correcta no existe.")
        self.options = options
        return self


class TrueFalseQuestionDraft(RagSchema):
    type: Literal["true_false"]
    statement: str = Field(min_length=1, max_length=2000)
    correct_answer: bool

    @model_validator(mode="after")
    def validate_statement(self) -> "TrueFalseQuestionDraft":
        self.statement = self.statement.strip()
        if not self.statement:
            raise ValueError("El enunciado no puede estar vacio.")
        return self


class OpenQuestionDraft(RagSchema):
    type: Literal["open"]
    statement: str = Field(min_length=1, max_length=2000)
    expected_answer: str = Field(min_length=1, max_length=4000)

    @model_validator(mode="after")
    def validate_text(self) -> "OpenQuestionDraft":
        self.statement = self.statement.strip()
        self.expected_answer = self.expected_answer.strip()
        if not self.statement or not self.expected_answer:
            raise ValueError("Enunciado y respuesta no pueden estar vacios.")
        return self


ExamQuestionDraft = (
    MultipleChoiceQuestionDraft | TrueFalseQuestionDraft | OpenQuestionDraft
)


class ExamDraft(RagSchema):
    title: str = Field(min_length=1, max_length=160)
    description: str | None = Field(max_length=1000)
    questions: list[ExamQuestionDraft] = Field(min_length=1, max_length=20)

    @model_validator(mode="after")
    def validate_unique_questions(self) -> "ExamDraft":
        self.title = self.title.strip()
        if not self.title:
            raise ValueError("El titulo no puede estar vacio.")
        normalized = [item.statement.strip().casefold() for item in self.questions]
        if len(normalized) != len(set(normalized)):
            raise ValueError("Las preguntas del examen deben ser unicas.")
        return self


class ExamGenerationRequest(RagSchema):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=1000)
    true_false_count: int = Field(default=3, ge=0, le=10)
    multiple_choice_count: int = Field(default=4, ge=0, le=10)
    open_count: int = Field(default=3, ge=0, le=10)
    model: str | None = Field(
        default=None,
        min_length=1,
        max_length=120,
        pattern=r"^[A-Za-z0-9._:/-]+$",
    )

    @model_validator(mode="after")
    def validate_question_count(self) -> "ExamGenerationRequest":
        total = self.true_false_count + self.multiple_choice_count + self.open_count
        if total < 1 or total > 20:
            raise ValueError("El examen debe contener entre 1 y 20 preguntas.")
        return self


class GeneratedQuestionOptionRead(RagSchema):
    option_id: UUID
    option_text: str
    option_order: int


class GeneratedExamQuestionRead(RagSchema):
    question_id: UUID
    type: Literal["multiple_choice", "true_false", "open"]
    statement: str
    question_order: int
    options: list[GeneratedQuestionOptionRead] = Field(default_factory=list)


class GeneratedExamRead(RagSchema):
    exam_id: UUID
    notebook_id: UUID
    name: str
    description: str | None = None
    status: str
    questions: list[GeneratedExamQuestionRead]


class ExamGenerationResponse(RagSchema):
    data: GeneratedExamRead
    sources: list[RagSource]
