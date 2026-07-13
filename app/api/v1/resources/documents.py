from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_documents_use_case
from app.application.usecases import DocumentUseCase
from app.domain.schemas.resources.documents import (
    DocumentListResponse,
    DocumentListRequest,
    DocumentPath,
    DocumentResponse,
)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    request: Annotated[DocumentListRequest, Depends()],
    use_case: Annotated[DocumentUseCase, Depends(get_documents_use_case)],
) -> DocumentListResponse:
    return await use_case.list(request)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    path: Annotated[DocumentPath, Depends()],
    use_case: Annotated[DocumentUseCase, Depends(get_documents_use_case)],
) -> DocumentResponse:
    return await use_case.get(path)
