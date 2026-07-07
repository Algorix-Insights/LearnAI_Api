from app.core.exceptions import EmptyPayloadError
from app.domain.schemas.resources.attempts import AttemptCreateRequest, AttemptUpdateRequest


class AttemptService:
    def prepare_create(self, request: AttemptCreateRequest) -> AttemptCreateRequest:
        return request

    def prepare_update(self, request: AttemptUpdateRequest) -> AttemptUpdateRequest:
        if not request.payload.model_dump(exclude_unset=True):
            raise EmptyPayloadError()
        return request
