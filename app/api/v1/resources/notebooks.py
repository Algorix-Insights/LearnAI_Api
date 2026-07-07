from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_notebook_tags_use_case, get_notebooks_use_case
from app.application.usecases import NotebookTagUseCase, NotebookUseCase
from app.domain.schemas.entities import NotebookCreate, NotebookUpdate
from app.domain.schemas.resources.notebooks import (
    NotebookCreateRequest,
    NotebookDeleteRequest,
    NotebookListResponse,
    NotebookListRequest,
    NotebookPath,
    NotebookResponse,
    NotebookTagPath,
    NotebookTagResponse,
    NotebookUpdateRequest,
)

router = APIRouter(prefix="/notebooks", tags=["notebooks"])


@router.get("", response_model=NotebookListResponse)
async def list_notebooks(
    request: Annotated[NotebookListRequest, Depends()],
    use_case: Annotated[NotebookUseCase, Depends(get_notebooks_use_case)],
) -> NotebookListResponse:
    return await use_case.list(request)


@router.post("", response_model=NotebookResponse, status_code=status.HTTP_201_CREATED)
async def create_notebook(
    payload: NotebookCreate,
    use_case: Annotated[NotebookUseCase, Depends(get_notebooks_use_case)],
) -> NotebookResponse:
    return await use_case.create(NotebookCreateRequest(payload=payload))


@router.get("/{notebook_id}", response_model=NotebookResponse)
async def get_notebook(
    path: Annotated[NotebookPath, Depends()],
    use_case: Annotated[NotebookUseCase, Depends(get_notebooks_use_case)],
) -> NotebookResponse:
    return await use_case.get(path)


@router.patch("/{notebook_id}", response_model=NotebookResponse)
async def update_notebook(
    path: Annotated[NotebookPath, Depends()],
    payload: NotebookUpdate,
    use_case: Annotated[NotebookUseCase, Depends(get_notebooks_use_case)],
) -> NotebookResponse:
    return await use_case.update(
        NotebookUpdateRequest(notebook_id=path.notebook_id, payload=payload)
    )


@router.delete("/{notebook_id}", response_model=NotebookResponse)
async def delete_notebook(
    path: Annotated[NotebookPath, Depends()],
    use_case: Annotated[NotebookUseCase, Depends(get_notebooks_use_case)],
) -> NotebookResponse:
    return await use_case.delete(NotebookDeleteRequest(notebook_id=path.notebook_id))


@router.post(
    "/{notebook_id}/tags/{tag_id}",
    response_model=NotebookTagResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["notebook-tags"],
)
async def attach_tag_to_notebook(
    path: Annotated[NotebookTagPath, Depends()],
    use_case: Annotated[NotebookTagUseCase, Depends(get_notebook_tags_use_case)],
) -> NotebookTagResponse:
    return await use_case.attach(path)


@router.delete(
    "/{notebook_id}/tags/{tag_id}",
    response_model=NotebookTagResponse,
    tags=["notebook-tags"],
)
async def detach_tag_from_notebook(
    path: Annotated[NotebookTagPath, Depends()],
    use_case: Annotated[NotebookTagUseCase, Depends(get_notebook_tags_use_case)],
) -> NotebookTagResponse:
    return await use_case.detach(path)
