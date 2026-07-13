from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from uuid import UUID

from fastapi import UploadFile

from app.application.usecases.rag_support.common import RagAccessPolicy
from app.application.usecases.rag_support.llm import RagLlmService
from app.core.config import Settings
from app.core.exceptions import BadRequestError, ResourceNotFoundError
from app.domain.schemas.entities import DocumentCreate, DocumentUpdate
from app.domain.schemas.resources.documents import (
    DocumentRepositoryCreateRequest,
    DocumentRepositoryDeleteRequest,
    DocumentRepositoryGetRequest,
    DocumentRepositoryUpdateRequest,
    DocumentResponse,
)
from app.domain.schemas.resources.rag import DocumentUploadResponse
from app.domain.services.rag import RagDocumentProcessor
from app.infra.repositories.document_chunks import DocumentChunkRepository
from app.infra.repositories.documents import DocumentRepository
from app.infra.storage import SupabaseStorage


logger = logging.getLogger("learnia.rag")

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_DOCUMENT_TEXT_CHARS = 250_000
MAX_DOCUMENT_CHUNKS = 80


class RagDocumentWorkflow:
    """Handles secure document ingestion, vectorization, and deletion."""

    def __init__(
        self,
        *,
        documents: DocumentRepository,
        chunks: DocumentChunkRepository,
        storage: SupabaseStorage,
        settings: Settings,
        document_processor: RagDocumentProcessor,
        llm: RagLlmService,
        policy: RagAccessPolicy,
    ) -> None:
        self.documents = documents
        self.chunks = chunks
        self.storage = storage
        self.settings = settings
        self.document_processor = document_processor
        self.llm = llm
        self.policy = policy

    async def upload_document(
        self,
        *,
        notebook_id: UUID,
        user_id: UUID,
        file: UploadFile,
        description: str | None = None,
    ) -> DocumentUploadResponse:
        await self.policy.require_manage_access(user_id=user_id, notebook_id=notebook_id)
        if file.size is not None and file.size > MAX_UPLOAD_BYTES:
            raise BadRequestError("El archivo supera el limite de 10 MB.")
        if description is not None and len(description) > 1000:
            raise BadRequestError("La descripcion supera el limite de 1000 caracteres.")
        content, suffix, mime_type = await self.document_processor.read_upload(file)
        if len(content) > MAX_UPLOAD_BYTES:
            raise BadRequestError("El archivo supera el limite de 10 MB.")
        content_hash = self.document_processor.content_hash(content)
        existing = await self.documents.get_by_hash(
            notebook_id=str(notebook_id), content_hash=content_hash
        )
        if existing:
            if existing.get("processing_status") != "failed":
                chunk_count = await self.chunks.count_for_document(str(existing["document_id"]))
                return DocumentUploadResponse(data={**existing, "chunks_count": chunk_count})
            await self.documents.delete(
                DocumentRepositoryDeleteRequest(document_id=UUID(str(existing["document_id"])))
            )
            if existing.get("storage_path"):
                try:
                    await self.storage.delete(
                        bucket=self.settings.documents_bucket,
                        paths=[str(existing["storage_path"])],
                    )
                except Exception:
                    logger.warning("rag_failed_document_cleanup_failed", exc_info=True)

        filename = file.filename or f"document{suffix}"
        if len(filename) > 255:
            raise BadRequestError("El nombre del archivo supera el limite de 255 caracteres.")
        storage_path = self.document_processor.storage_path(notebook_id, filename, suffix)
        # Reserve before CPU-heavy parsing/chunking as well as before the provider
        # call, so malformed authenticated uploads cannot bypass the durable ceiling.
        await self.policy.reserve_ai_usage(user_id, "document_embedding")
        text = await asyncio.to_thread(
            self.document_processor.extract_text,
            content,
            suffix,
        )
        if len(text) > MAX_DOCUMENT_TEXT_CHARS:
            raise BadRequestError("El documento extraido supera el limite de 250000 caracteres.")
        chunks = await asyncio.to_thread(self.document_processor.chunk_text, text)
        if len(chunks) > MAX_DOCUMENT_CHUNKS:
            raise BadRequestError("El documento genera demasiados fragmentos para procesarlo.")
        await self.storage.upload(
            bucket=self.settings.documents_bucket,
            path=storage_path,
            content=content,
            content_type=mime_type,
        )
        try:
            document = await self.documents.create(
                DocumentRepositoryCreateRequest(
                    payload=DocumentCreate(
                        notebook_id=notebook_id,
                        name=filename,
                        description=description,
                        source_type=self.document_processor.source_type(suffix),
                        storage_path=storage_path,
                        processing_status="processing",
                        mime_type=mime_type,
                        content_text=text,
                        content_hash=content_hash,
                        size_bytes=len(content),
                    )
                )
            )
        except Exception:
            await self.storage.delete(
                bucket=self.settings.documents_bucket,
                paths=[storage_path],
            )
            raise
        try:
            embeddings = await self.llm.embed(chunks)
            await self.chunks.create_many(
                [
                    {
                        "document_id": document["document_id"],
                        "chunk_index": index,
                        "content": chunk,
                        "embedding": embeddings[index],
                        "model": self.settings.openrouter_embedding_model,
                        "token_count": len(chunk.split()),
                    }
                    for index, chunk in enumerate(chunks)
                ]
            )
            document = await self._update_document_status(str(document["document_id"]), "completed")
        except Exception:
            await self._update_document_status(str(document["document_id"]), "failed")
            raise
        await self.policy.record_server_activity(
            actor_id=user_id,
            notebook_id=notebook_id,
            activity_type="document_uploaded",
            quantity=1,
            idempotency_key=f"server:document:{document['document_id']}",
            metadata={"document_id": str(document["document_id"])},
        )
        return DocumentUploadResponse(data={**document, "chunks_count": len(chunks)})

    async def delete_document(
        self,
        *,
        notebook_id: UUID,
        document_id: UUID,
        user_id: UUID,
    ) -> DocumentResponse:
        await self.policy.require_manage_access(user_id=user_id, notebook_id=notebook_id)
        document = await self.documents.get_internal(
            DocumentRepositoryGetRequest(document_id=document_id)
        )
        if document is None or str(document.get("notebook_id")) != str(notebook_id):
            raise ResourceNotFoundError()
        deleted = await self.documents.delete(
            DocumentRepositoryDeleteRequest(document_id=document_id)
        )
        if deleted is None:
            raise ResourceNotFoundError()
        storage_path = document.get("storage_path")
        if storage_path:
            try:
                await self.storage.delete(
                    bucket=self.settings.documents_bucket,
                    paths=[str(storage_path)],
                )
            except Exception:
                logger.warning("rag_document_storage_cleanup_failed", exc_info=True)
        return DocumentResponse(data=document)

    async def _update_document_status(self, document_id: str, status: str) -> dict:
        data = await self.documents.update(
            DocumentRepositoryUpdateRequest(
                document_id=UUID(document_id),
                payload=DocumentUpdate(processing_status=status),
                updated_at=datetime.now(UTC),
            )
        )
        if data is None:
            raise ResourceNotFoundError()
        return data
