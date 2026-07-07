from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.schemas.entities import DocumentCreate, DocumentUpdate


class DocumentSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DocumentListRequest(DocumentSchema):
    limit: int = Field(default=100, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class DocumentPath(DocumentSchema):
    document_id: UUID


class DocumentCreateRequest(DocumentSchema):
    payload: DocumentCreate


class DocumentUpdateRequest(DocumentSchema):
    document_id: UUID
    payload: DocumentUpdate


class DocumentDeleteRequest(DocumentSchema):
    document_id: UUID


class DocumentRepositoryListRequest(DocumentListRequest):
    pass


class DocumentRepositoryGetRequest(DocumentPath):
    pass


class DocumentRepositoryCreateRequest(DocumentCreateRequest):
    pass


class DocumentRepositoryUpdateRequest(DocumentUpdateRequest):
    updated_at: datetime


class DocumentRepositoryDeleteRequest(DocumentDeleteRequest):
    pass
