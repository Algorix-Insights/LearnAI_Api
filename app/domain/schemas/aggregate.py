from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AggregateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ListItemsRequest(AggregateSchema):
    limit: int = Field(default=100, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class ItemRequest(AggregateSchema):
    item_id: str


class UserPath(AggregateSchema):
    user_id: UUID

    def to_item_request(self) -> "ItemRequest":
        return ItemRequest(item_id=str(self.user_id))


class NotebookPath(AggregateSchema):
    notebook_id: UUID

    def to_item_request(self) -> "ItemRequest":
        return ItemRequest(item_id=str(self.notebook_id))


class RoomPath(AggregateSchema):
    room_id: UUID

    def to_item_request(self) -> "ItemRequest":
        return ItemRequest(item_id=str(self.room_id))


class StudyMemberPath(AggregateSchema):
    member_id: UUID

    def to_item_request(self) -> "ItemRequest":
        return ItemRequest(item_id=str(self.member_id))


class ExamPath(AggregateSchema):
    exam_id: UUID

    def to_item_request(self) -> "ItemRequest":
        return ItemRequest(item_id=str(self.exam_id))


class QuestionPath(AggregateSchema):
    question_id: UUID

    def to_item_request(self) -> "ItemRequest":
        return ItemRequest(item_id=str(self.question_id))


class QuestionOptionPath(AggregateSchema):
    option_id: UUID

    def to_item_request(self) -> "ItemRequest":
        return ItemRequest(item_id=str(self.option_id))


class AttemptPath(AggregateSchema):
    attempt_id: UUID

    def to_item_request(self) -> "ItemRequest":
        return ItemRequest(item_id=str(self.attempt_id))


class UserAnswerPath(AggregateSchema):
    answer_id: UUID

    def to_item_request(self) -> "ItemRequest":
        return ItemRequest(item_id=str(self.answer_id))


class FlashcardPath(AggregateSchema):
    flashcard_id: UUID

    def to_item_request(self) -> "ItemRequest":
        return ItemRequest(item_id=str(self.flashcard_id))


class DocumentPath(AggregateSchema):
    document_id: UUID

    def to_item_request(self) -> "ItemRequest":
        return ItemRequest(item_id=str(self.document_id))


class DocumentChunkPath(AggregateSchema):
    chunk_id: UUID

    def to_item_request(self) -> "ItemRequest":
        return ItemRequest(item_id=str(self.chunk_id))


class TagPath(AggregateSchema):
    tag_id: UUID

    def to_item_request(self) -> "ItemRequest":
        return ItemRequest(item_id=str(self.tag_id))


class CreateItemRequest(AggregateSchema):
    payload: BaseModel


class UpdateItemRequest(AggregateSchema):
    item_id: str
    payload: BaseModel


class DeleteItemRequest(AggregateSchema):
    item_id: str


class RepositoryListItemsRequest(AggregateSchema):
    limit: int = Field(default=100, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class RepositoryCreateItemRequest(AggregateSchema):
    payload: dict[str, Any]


class RepositoryItemRequest(AggregateSchema):
    item_id: str


class RepositoryUpdateItemRequest(AggregateSchema):
    item_id: str
    payload: dict[str, Any]


class RepositoryFilterRequest(AggregateSchema):
    filters: dict[str, Any]


class RepositoryUpdateByFilterRequest(AggregateSchema):
    filters: dict[str, Any]
    payload: dict[str, Any]


class NotebookTagPath(AggregateSchema):
    notebook_id: UUID
    tag_id: UUID


class AddRoomMemberRequest(AggregateSchema):
    member_id: UUID
    role: str = Field(default="member", pattern="^(member|admin)$")


class RoomMemberPath(AggregateSchema):
    room_id: UUID
    member_id: UUID


class AddExamQuestionRequest(AggregateSchema):
    question_id: UUID
    question_order: int = Field(gt=0)
    points: Decimal = Field(default=Decimal("1"), ge=0)


class ExamQuestionPath(AggregateSchema):
    exam_id: UUID
    question_id: UUID


class PersonalNotebookPath(AggregateSchema):
    user_id: UUID
    notebook_id: UUID


class AddRoomNotebookRequest(AggregateSchema):
    notebook_id: UUID
    created_by: UUID


class RoomNotebookPath(AggregateSchema):
    room_id: UUID
    notebook_id: UUID
