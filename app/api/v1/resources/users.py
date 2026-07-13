from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Header, UploadFile, status

from app.api.dependencies import (
    get_current_user,
    get_user_profile_use_case,
    get_user_statistics_use_case,
    get_users_use_case,
)
from app.application.usecases import UserUseCase
from app.application.usecases.user_profile import UserProfileUseCase
from app.application.usecases.user_statistics import UserStatisticsUseCase
from app.core.exceptions import UnauthorizedError
from app.domain.schemas.entities import UserUpdate
from app.domain.schemas.resources.user_profile import (
    ProfilePhotoDeleteResponse,
    ProfilePhotoResponse,
    UserSelfUpdate,
)
from app.domain.schemas.resources.user_statistics import (
    LearningEventCreate,
    LearningEventResponse,
    UserStatisticsRequest,
    UserStatisticsResponse,
)
from app.domain.schemas.resources.users import (
    UserListResponse,
    UserListRequest,
    UserPath,
    UserRead,
    UserResponse,
    UserUpdateRequest,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_my_profile(
    current_user: Annotated[UserRead, Depends(get_current_user)],
) -> UserResponse:
    return UserResponse(data=current_user)


@router.patch("/me", response_model=UserResponse)
async def update_my_profile(
    payload: UserSelfUpdate,
    current_user: Annotated[UserRead, Depends(get_current_user)],
    use_case: Annotated[UserUseCase, Depends(get_users_use_case)],
) -> UserResponse:
    user_id = _actor_id(current_user)
    return await use_case.update(
        UserUpdateRequest(
            user_id=user_id,
            payload=UserUpdate(**payload.model_dump(exclude_unset=True)),
        )
    )


@router.post(
    "/me/profile-photo",
    response_model=ProfilePhotoResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_my_profile_photo(
    file: Annotated[UploadFile, File()],
    current_user: Annotated[UserRead, Depends(get_current_user)],
    use_case: Annotated[UserProfileUseCase, Depends(get_user_profile_use_case)],
) -> ProfilePhotoResponse:
    return await use_case.upload_photo(user_id=_actor_id(current_user), file=file)


@router.get("/me/profile-photo", response_model=ProfilePhotoResponse)
async def get_my_profile_photo(
    current_user: Annotated[UserRead, Depends(get_current_user)],
    use_case: Annotated[UserProfileUseCase, Depends(get_user_profile_use_case)],
) -> ProfilePhotoResponse:
    return await use_case.get_photo(user_id=_actor_id(current_user))


@router.delete("/me/profile-photo", response_model=ProfilePhotoDeleteResponse)
async def delete_my_profile_photo(
    current_user: Annotated[UserRead, Depends(get_current_user)],
    use_case: Annotated[UserProfileUseCase, Depends(get_user_profile_use_case)],
) -> ProfilePhotoDeleteResponse:
    return await use_case.delete_photo(user_id=_actor_id(current_user))


@router.get("/me/statistics", response_model=UserStatisticsResponse)
async def get_my_statistics(
    request: Annotated[UserStatisticsRequest, Depends()],
    current_user: Annotated[UserRead, Depends(get_current_user)],
    use_case: Annotated[
        UserStatisticsUseCase, Depends(get_user_statistics_use_case)
    ],
) -> UserStatisticsResponse:
    return await use_case.get(_actor_id(current_user), request)


@router.post(
    "/me/learning-events",
    response_model=LearningEventResponse,
    status_code=status.HTTP_201_CREATED,
)
async def record_my_learning_event(
    payload: LearningEventCreate,
    idempotency_key: Annotated[
        str,
        Header(
            alias="Idempotency-Key",
            min_length=16,
            max_length=128,
            pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{15,127}$",
        ),
    ],
    current_user: Annotated[UserRead, Depends(get_current_user)],
    use_case: Annotated[
        UserStatisticsUseCase, Depends(get_user_statistics_use_case)
    ],
) -> LearningEventResponse:
    return await use_case.record(_actor_id(current_user), payload, idempotency_key)


# Compatibility reads remain self-only. User creation/deletion and arbitrary profile
# mutation are intentionally absent: Supabase Auth owns account lifecycle.
@router.get("", response_model=UserListResponse)
async def list_users(
    request: Annotated[UserListRequest, Depends()],
    current_user: Annotated[UserRead, Depends(get_current_user)],
) -> UserListResponse:
    data = [current_user] if request.offset == 0 else []
    return UserListResponse(data=data, limit=request.limit, offset=request.offset)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    path: Annotated[UserPath, Depends()],
    current_user: Annotated[UserRead, Depends(get_current_user)],
) -> UserResponse:
    actor_id = _actor_id(current_user)
    if path.user_id != actor_id:
        # Do not disclose whether another profile exists.
        from app.core.exceptions import ResourceNotFoundError

        raise ResourceNotFoundError()
    return UserResponse(data=current_user)


def _actor_id(current_user: UserRead) -> UUID:
    if current_user.user_id is None:
        raise UnauthorizedError()
    return current_user.user_id
