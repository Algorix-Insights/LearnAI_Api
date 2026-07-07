from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_room_members_use_case, get_room_notebooks_use_case
from app.api.dependencies import get_rooms_use_case
from app.application.usecases import RoomMemberUseCase, RoomNotebookUseCase, RoomUseCase
from app.domain.schemas import (
    AddRoomMemberRequest,
    AddRoomNotebookRequest,
    CreateItemRequest,
    CrudItemResponse,
    CrudListResponse,
    DeleteItemRequest,
    ListItemsRequest,
    RoomMemberPath,
    RoomNotebookPath,
    RoomPath,
    UpdateItemRequest,
)
from app.domain.schemas.entities import RoomCreate, RoomUpdate

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.get("", response_model=CrudListResponse)
async def list_rooms(
    request: Annotated[ListItemsRequest, Depends()],
    use_case: Annotated[RoomUseCase, Depends(get_rooms_use_case)],
) -> CrudListResponse:
    return await use_case.list(request)


@router.post("", response_model=CrudItemResponse, status_code=status.HTTP_201_CREATED)
async def create_room(
    payload: RoomCreate,
    use_case: Annotated[RoomUseCase, Depends(get_rooms_use_case)],
) -> CrudItemResponse:
    return await use_case.create(CreateItemRequest(payload=payload))


@router.get("/{room_id}", response_model=CrudItemResponse)
async def get_room(
    path: Annotated[RoomPath, Depends()],
    use_case: Annotated[RoomUseCase, Depends(get_rooms_use_case)],
) -> CrudItemResponse:
    return await use_case.get(path.to_item_request())


@router.patch("/{room_id}", response_model=CrudItemResponse)
async def update_room(
    path: Annotated[RoomPath, Depends()],
    payload: RoomUpdate,
    use_case: Annotated[RoomUseCase, Depends(get_rooms_use_case)],
) -> CrudItemResponse:
    return await use_case.update(UpdateItemRequest(item_id=str(path.room_id), payload=payload))


@router.delete("/{room_id}", response_model=CrudItemResponse)
async def delete_room(
    path: Annotated[RoomPath, Depends()],
    use_case: Annotated[RoomUseCase, Depends(get_rooms_use_case)],
) -> CrudItemResponse:
    return await use_case.delete(DeleteItemRequest(item_id=str(path.room_id)))


@router.post(
    "/{room_id}/members",
    response_model=CrudItemResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["room-members"],
)
async def add_member_to_room(
    path: Annotated[RoomPath, Depends()],
    payload: AddRoomMemberRequest,
    use_case: Annotated[RoomMemberUseCase, Depends(get_room_members_use_case)],
) -> CrudItemResponse:
    return await use_case.add(str(path.room_id), payload)


@router.delete(
    "/{room_id}/members/{member_id}",
    response_model=CrudItemResponse,
    tags=["room-members"],
)
async def remove_member_from_room(
    path: Annotated[RoomMemberPath, Depends()],
    use_case: Annotated[RoomMemberUseCase, Depends(get_room_members_use_case)],
) -> CrudItemResponse:
    return await use_case.remove(path)


@router.post(
    "/{room_id}/notebooks",
    response_model=CrudItemResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["room-notebooks"],
)
async def add_room_notebook(
    path: Annotated[RoomPath, Depends()],
    payload: AddRoomNotebookRequest,
    use_case: Annotated[RoomNotebookUseCase, Depends(get_room_notebooks_use_case)],
) -> CrudItemResponse:
    return await use_case.add(str(path.room_id), payload)


@router.delete(
    "/{room_id}/notebooks/{notebook_id}",
    response_model=CrudItemResponse,
    tags=["room-notebooks"],
)
async def remove_room_notebook(
    path: Annotated[RoomNotebookPath, Depends()],
    use_case: Annotated[RoomNotebookUseCase, Depends(get_room_notebooks_use_case)],
) -> CrudItemResponse:
    return await use_case.remove(path)
