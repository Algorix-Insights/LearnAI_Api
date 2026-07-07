from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_personal_notebooks_use_case, get_users_use_case
from app.application.usecases import PersonalNotebookUseCase, UserUseCase
from app.domain.schemas import CrudItemResponse, CrudListResponse
from app.domain.schemas.entities import UserCreate, UserUpdate
from app.domain.schemas.resources.users import (
    PersonalNotebookPath,
    UserCreateRequest,
    UserDeleteRequest,
    UserListRequest,
    UserPath,
    UserUpdateRequest,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=CrudListResponse)
async def list_users(
    request: Annotated[UserListRequest, Depends()],
    use_case: Annotated[UserUseCase, Depends(get_users_use_case)],
) -> CrudListResponse:
    return await use_case.list(request)


@router.post("", response_model=CrudItemResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    use_case: Annotated[UserUseCase, Depends(get_users_use_case)],
) -> CrudItemResponse:
    return await use_case.create(UserCreateRequest(payload=payload))


@router.get("/{user_id}", response_model=CrudItemResponse)
async def get_user(
    path: Annotated[UserPath, Depends()],
    use_case: Annotated[UserUseCase, Depends(get_users_use_case)],
) -> CrudItemResponse:
    return await use_case.get(path)


@router.patch("/{user_id}", response_model=CrudItemResponse)
async def update_user(
    path: Annotated[UserPath, Depends()],
    payload: UserUpdate,
    use_case: Annotated[UserUseCase, Depends(get_users_use_case)],
) -> CrudItemResponse:
    return await use_case.update(UserUpdateRequest(user_id=path.user_id, payload=payload))


@router.delete("/{user_id}", response_model=CrudItemResponse)
async def delete_user(
    path: Annotated[UserPath, Depends()],
    use_case: Annotated[UserUseCase, Depends(get_users_use_case)],
) -> CrudItemResponse:
    return await use_case.delete(UserDeleteRequest(user_id=path.user_id))


@router.post(
    "/{user_id}/notebooks/{notebook_id}",
    response_model=CrudItemResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["personal-notebooks"],
)
async def add_personal_notebook(
    path: Annotated[PersonalNotebookPath, Depends()],
    use_case: Annotated[
        PersonalNotebookUseCase, Depends(get_personal_notebooks_use_case)
    ],
) -> CrudItemResponse:
    return await use_case.add(path)


@router.delete(
    "/{user_id}/notebooks/{notebook_id}",
    response_model=CrudItemResponse,
    tags=["personal-notebooks"],
)
async def remove_personal_notebook(
    path: Annotated[PersonalNotebookPath, Depends()],
    use_case: Annotated[
        PersonalNotebookUseCase, Depends(get_personal_notebooks_use_case)
    ],
) -> CrudItemResponse:
    return await use_case.remove(path)
