from hashlib import sha256

from app.core.exceptions import EmptyPayloadError
from app.domain.schemas.resources.documents import DocumentCreateRequest, DocumentUpdateRequest


class DocumentService:
    def prepare_create(self, request: DocumentCreateRequest) -> DocumentCreateRequest:
        if request.payload.content_hash:
            return request
        source = request.payload.content_text or request.payload.storage_path or request.payload.name
        payload = request.payload.model_copy(
            update={"content_hash": sha256(source.encode()).hexdigest()}
        )
        return DocumentCreateRequest(payload=payload)

    def prepare_update(self, request: DocumentUpdateRequest) -> DocumentUpdateRequest:
        if not request.payload.model_dump(exclude_unset=True):
            raise EmptyPayloadError()
        return request
