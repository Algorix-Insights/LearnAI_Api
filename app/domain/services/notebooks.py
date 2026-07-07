from app.core.exceptions import EmptyPayloadError
from app.domain.schemas.resources.notebooks import NotebookCreateRequest, NotebookUpdateRequest


class NotebookService:
    def prepare_create(self, request: NotebookCreateRequest) -> NotebookCreateRequest:
        payload = request.payload.model_copy(update={"name": request.payload.name.strip()})
        return NotebookCreateRequest(payload=payload)

    def prepare_update(self, request: NotebookUpdateRequest) -> NotebookUpdateRequest:
        update_data = request.payload.model_dump(exclude_unset=True)
        if not update_data:
            raise EmptyPayloadError()
        if request.payload.name is None:
            return request
        payload = request.payload.model_copy(update={"name": request.payload.name.strip()})
        return NotebookUpdateRequest(notebook_id=request.notebook_id, payload=payload)
