from app.core.exceptions import EmptyPayloadError
from app.domain.schemas.entities import UserUpdate
from app.domain.schemas.resources.users import UserCreateRequest, UserUpdateRequest


class UserService:
    def prepare_create(self, request: UserCreateRequest) -> UserCreateRequest:
        payload = request.payload.model_copy(
            update={"email": request.payload.email.strip().lower()}
        )
        return UserCreateRequest(payload=payload)

    def prepare_update(self, request: UserUpdateRequest) -> UserUpdateRequest:
        update_data = request.payload.model_dump(exclude_unset=True)
        if not update_data:
            raise EmptyPayloadError()
        payload = self._normalize_update(request.payload)
        return UserUpdateRequest(user_id=request.user_id, payload=payload)

    def _normalize_update(self, payload: UserUpdate) -> UserUpdate:
        if payload.email is None:
            return payload
        return payload.model_copy(update={"email": payload.email.strip().lower()})
