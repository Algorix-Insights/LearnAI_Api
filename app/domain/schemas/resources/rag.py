from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RagSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DocumentUploadResult(BaseModel):
    model_config = ConfigDict(extra="allow")

    document_id: UUID | None = None
    notebook_id: UUID | None = None
    name: str | None = None
    source_type: str | None = None
    storage_path: str | None = None
    processing_status: str | None = None
    mime_type: str | None = None
    content_hash: str | None = None
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
    user_id: UUID
    name: str = "Nueva conversacion"


class ConversationRead(BaseModel):
    model_config = ConfigDict(extra="allow")

    conversation_id: UUID | None = None
    notebook_id: UUID | None = None
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
    user_id: UUID
    content: str = Field(min_length=1)
    model: str | None = None


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
