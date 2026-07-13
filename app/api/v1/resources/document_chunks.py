from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_document_chunks_use_case
from app.application.usecases import DocumentChunkUseCase
from app.domain.schemas.resources.document_chunks import (
    DocumentChunkListResponse,
    DocumentChunkListRequest,
    DocumentChunkPath,
    DocumentChunkResponse,
)

router = APIRouter(prefix="/document-chunks", tags=["document-chunks"])


@router.get("", response_model=DocumentChunkListResponse)
async def list_document_chunks(
    request: Annotated[DocumentChunkListRequest, Depends()],
    use_case: Annotated[DocumentChunkUseCase, Depends(get_document_chunks_use_case)],
) -> DocumentChunkListResponse:
    return await use_case.list(request)


@router.get("/{chunk_id}", response_model=DocumentChunkResponse)
async def get_document_chunk(
    path: Annotated[DocumentChunkPath, Depends()],
    use_case: Annotated[DocumentChunkUseCase, Depends(get_document_chunks_use_case)],
) -> DocumentChunkResponse:
    return await use_case.get(path)
