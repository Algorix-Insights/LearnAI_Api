from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.schemas.entities import ExamCreate, ExamUpdate


class ExamSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ExamRead(BaseModel):
    model_config = ConfigDict(extra="allow")

    exam_id: UUID | None = None
    notebook_id: UUID | None = None
    name: str | None = None
    description: str | None = None
    status: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ExamResponse(ExamSchema):
    data: ExamRead


class ExamListResponse(ExamSchema):
    data: list[ExamRead]
    limit: int
    offset: int


class ExamListRequest(ExamSchema):
    limit: int = Field(default=100, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class ExamPath(ExamSchema):
    exam_id: UUID


class ExamCreateRequest(ExamSchema):
    payload: ExamCreate


class ExamUpdateRequest(ExamSchema):
    exam_id: UUID
    payload: ExamUpdate


class ExamDeleteRequest(ExamSchema):
    exam_id: UUID


class ExamRepositoryListRequest(ExamListRequest):
    pass


class ExamRepositoryGetRequest(ExamPath):
    pass


class ExamRepositoryCreateRequest(ExamCreateRequest):
    pass


class ExamRepositoryUpdateRequest(ExamUpdateRequest):
    updated_at: datetime


class ExamRepositoryDeleteRequest(ExamDeleteRequest):
    pass


class AddExamQuestionRequest(ExamSchema):
    question_id: UUID
    question_order: int = Field(gt=0)
    points: Decimal = Field(default=Decimal("1"), ge=0)


class ExamQuestionPath(ExamSchema):
    exam_id: UUID
    question_id: UUID


class ExamQuestionRepositoryCreateRequest(ExamSchema):
    exam_id: UUID
    question_id: UUID
    question_order: int = Field(gt=0)
    points: Decimal = Field(default=Decimal("1"), ge=0)


class ExamQuestionRepositoryDeleteRequest(ExamQuestionPath):
    pass


class ExamQuestionRead(BaseModel):
    model_config = ConfigDict(extra="allow")

    exam_id: UUID | None = None
    question_id: UUID | None = None
    question_order: int | None = None
    points: Decimal | None = None


class ExamQuestionResponse(ExamSchema):
    data: ExamQuestionRead
