from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_document_chunks_use_case
from app.application.usecases import DocumentChunkUseCase
from app.domain.schemas import CrudItemResponse, CrudListResponse
from app.domain.schemas.entities import DocumentChunkCreate, DocumentChunkUpdate
from app.domain.schemas.resources.document_chunks import (
    DocumentChunkCreateRequest,
    DocumentChunkDeleteRequest,
    DocumentChunkListRequest,
    DocumentChunkPath,
    DocumentChunkUpdateRequest,
)

router = APIRouter(prefix="/document-chunks", tags=["document-chunks"])


@router.get("", response_model=CrudListResponse)
async def list_document_chunks(
    request: Annotated[DocumentChunkListRequest, Depends()],
    use_case: Annotated[DocumentChunkUseCase, Depends(get_document_chunks_use_case)],
) -> CrudListResponse:
    return await use_case.list(request)


@router.post("", response_model=CrudItemResponse, status_code=status.HTTP_201_CREATED)
async def create_document_chunk(
    payload: DocumentChunkCreate,
    use_case: Annotated[DocumentChunkUseCase, Depends(get_document_chunks_use_case)],
) -> CrudItemResponse:
    return await use_case.create(DocumentChunkCreateRequest(payload=payload))


@router.get("/{chunk_id}", response_model=CrudItemResponse)
async def get_document_chunk(
    path: Annotated[DocumentChunkPath, Depends()],
    use_case: Annotated[DocumentChunkUseCase, Depends(get_document_chunks_use_case)],
) -> CrudItemResponse:
    return await use_case.get(path)


@router.patch("/{chunk_id}", response_model=CrudItemResponse)
async def update_document_chunk(
    path: Annotated[DocumentChunkPath, Depends()],
    payload: DocumentChunkUpdate,
    use_case: Annotated[DocumentChunkUseCase, Depends(get_document_chunks_use_case)],
) -> CrudItemResponse:
    return await use_case.update(
        DocumentChunkUpdateRequest(chunk_id=path.chunk_id, payload=payload)
    )


@router.delete("/{chunk_id}", response_model=CrudItemResponse)
async def delete_document_chunk(
    path: Annotated[DocumentChunkPath, Depends()],
    use_case: Annotated[DocumentChunkUseCase, Depends(get_document_chunks_use_case)],
) -> CrudItemResponse:
    return await use_case.delete(DocumentChunkDeleteRequest(chunk_id=path.chunk_id))
