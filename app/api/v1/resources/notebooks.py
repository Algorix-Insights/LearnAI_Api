from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_notebook_tags_use_case, get_notebooks_use_case
from app.application.usecases import NotebookTagUseCase, NotebookUseCase
from app.domain.schemas import (
    CreateItemRequest,
    CrudItemResponse,
    CrudListResponse,
    DeleteItemRequest,
    ListItemsRequest,
    NotebookPath,
    NotebookTagPath,
    UpdateItemRequest,
)
from app.domain.schemas.entities import NotebookCreate, NotebookUpdate

router = APIRouter(prefix="/notebooks", tags=["notebooks"])


@router.get("", response_model=CrudListResponse)
async def list_notebooks(
    request: Annotated[ListItemsRequest, Depends()],
    use_case: Annotated[NotebookUseCase, Depends(get_notebooks_use_case)],
) -> CrudListResponse:
    return await use_case.list(request)


@router.post("", response_model=CrudItemResponse, status_code=status.HTTP_201_CREATED)
async def create_notebook(
    payload: NotebookCreate,
    use_case: Annotated[NotebookUseCase, Depends(get_notebooks_use_case)],
) -> CrudItemResponse:
    return await use_case.create(CreateItemRequest(payload=payload))


@router.get("/{notebook_id}", response_model=CrudItemResponse)
async def get_notebook(
    path: Annotated[NotebookPath, Depends()],
    use_case: Annotated[NotebookUseCase, Depends(get_notebooks_use_case)],
) -> CrudItemResponse:
    return await use_case.get(path.to_item_request())


@router.patch("/{notebook_id}", response_model=CrudItemResponse)
async def update_notebook(
    path: Annotated[NotebookPath, Depends()],
    payload: NotebookUpdate,
    use_case: Annotated[NotebookUseCase, Depends(get_notebooks_use_case)],
) -> CrudItemResponse:
    return await use_case.update(
        UpdateItemRequest(item_id=str(path.notebook_id), payload=payload)
    )


@router.delete("/{notebook_id}", response_model=CrudItemResponse)
async def delete_notebook(
    path: Annotated[NotebookPath, Depends()],
    use_case: Annotated[NotebookUseCase, Depends(get_notebooks_use_case)],
) -> CrudItemResponse:
    return await use_case.delete(DeleteItemRequest(item_id=str(path.notebook_id)))


@router.post(
    "/{notebook_id}/tags/{tag_id}",
    response_model=CrudItemResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["notebook-tags"],
)
async def attach_tag_to_notebook(
    path: Annotated[NotebookTagPath, Depends()],
    use_case: Annotated[NotebookTagUseCase, Depends(get_notebook_tags_use_case)],
) -> CrudItemResponse:
    return await use_case.attach(path)


@router.delete(
    "/{notebook_id}/tags/{tag_id}",
    response_model=CrudItemResponse,
    tags=["notebook-tags"],
)
async def detach_tag_from_notebook(
    path: Annotated[NotebookTagPath, Depends()],
    use_case: Annotated[NotebookTagUseCase, Depends(get_notebook_tags_use_case)],
) -> CrudItemResponse:
    return await use_case.detach(path)
