from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.schemas.entities import DocumentChunkCreate, DocumentChunkUpdate


class DocumentChunkSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DocumentChunkRead(BaseModel):
    model_config = ConfigDict(extra="ignore")

    chunk_id: UUID | None = None
    document_id: UUID | None = None
    chunk_index: int | None = None
    content: str | None = None
    model: str | None = None
    token_count: int | None = None
    created_at: str | None = None


class DocumentChunkResponse(DocumentChunkSchema):
    data: DocumentChunkRead


class DocumentChunkListResponse(DocumentChunkSchema):
    data: list[DocumentChunkRead]
    limit: int
    offset: int


class DocumentChunkListRequest(DocumentChunkSchema):
    limit: int = Field(default=100, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class DocumentChunkPath(DocumentChunkSchema):
    chunk_id: UUID


class DocumentChunkCreateRequest(DocumentChunkSchema):
    payload: DocumentChunkCreate


class DocumentChunkUpdateRequest(DocumentChunkSchema):
    chunk_id: UUID
    payload: DocumentChunkUpdate


class DocumentChunkDeleteRequest(DocumentChunkSchema):
    chunk_id: UUID


class DocumentChunkRepositoryListRequest(DocumentChunkListRequest):
    pass


class DocumentChunkRepositoryGetRequest(DocumentChunkPath):
    pass


class DocumentChunkRepositoryCreateRequest(DocumentChunkCreateRequest):
    pass


class DocumentChunkRepositoryUpdateRequest(DocumentChunkUpdateRequest):
    pass


class DocumentChunkRepositoryDeleteRequest(DocumentChunkDeleteRequest):
    pass
