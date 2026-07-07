from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_documents_use_case
from app.application.usecases import DocumentUseCase
from app.domain.schemas import (
    CreateItemRequest,
    CrudItemResponse,
    CrudListResponse,
    DeleteItemRequest,
    DocumentPath,
    ListItemsRequest,
    UpdateItemRequest,
)
from app.domain.schemas.entities import DocumentCreate, DocumentUpdate

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=CrudListResponse)
async def list_documents(
    request: Annotated[ListItemsRequest, Depends()],
    use_case: Annotated[DocumentUseCase, Depends(get_documents_use_case)],
) -> CrudListResponse:
    return await use_case.list(request)


@router.post("", response_model=CrudItemResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    payload: DocumentCreate,
    use_case: Annotated[DocumentUseCase, Depends(get_documents_use_case)],
) -> CrudItemResponse:
    return await use_case.create(CreateItemRequest(payload=payload))


@router.get("/{document_id}", response_model=CrudItemResponse)
async def get_document(
    path: Annotated[DocumentPath, Depends()],
    use_case: Annotated[DocumentUseCase, Depends(get_documents_use_case)],
) -> CrudItemResponse:
    return await use_case.get(path.to_item_request())


@router.patch("/{document_id}", response_model=CrudItemResponse)
async def update_document(
    path: Annotated[DocumentPath, Depends()],
    payload: DocumentUpdate,
    use_case: Annotated[DocumentUseCase, Depends(get_documents_use_case)],
) -> CrudItemResponse:
    return await use_case.update(
        UpdateItemRequest(item_id=str(path.document_id), payload=payload)
    )


@router.delete("/{document_id}", response_model=CrudItemResponse)
async def delete_document(
    path: Annotated[DocumentPath, Depends()],
    use_case: Annotated[DocumentUseCase, Depends(get_documents_use_case)],
) -> CrudItemResponse:
    return await use_case.delete(DeleteItemRequest(item_id=str(path.document_id)))
