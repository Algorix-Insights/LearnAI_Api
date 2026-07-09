from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Mapping, Sequence
from uuid import UUID

from fastapi import UploadFile

from app.application.interfaces import OpenRouterGateway, OpenRouterMessage
from app.core.config import Settings
from app.core.exceptions import BadRequestError, ForbiddenError, ResourceNotFoundError
from app.domain.schemas.entities import DocumentCreate, DocumentUpdate, UserUpdate
from app.domain.schemas.resources.documents import (
    DocumentRepositoryCreateRequest,
    DocumentRepositoryUpdateRequest,
)
from app.domain.schemas.resources.rag import (
    ChatRequest,
    ChatResponse,
    ConversationCreateRequest,
    ConversationListResponse,
    ConversationResponse,
    DocumentUploadResponse,
    MessageListResponse,
    ProfilePhotoResponse,
)
from app.domain.schemas.resources.users import UserRepositoryGetRequest, UserRepositoryUpdateRequest
from app.domain.services.rag import ProfileImageProcessor, RagDocumentProcessor
from app.infra.repositories.document_chunks import DocumentChunkRepository
from app.infra.repositories.documents import DocumentRepository
from app.infra.repositories.rag import (
    ConversationRepository,
    NotebookAccessRepository,
    RagSearchRepository,
)
from app.infra.repositories.users import UserRepository
from app.infra.storage import SupabaseStorage


class RagUseCase:
    def __init__(
        self,
        *,
        documents: DocumentRepository,
        chunks: DocumentChunkRepository,
        conversations: ConversationRepository,
        search: RagSearchRepository,
        access: NotebookAccessRepository,
        users: UserRepository,
        storage: SupabaseStorage,
        llm: OpenRouterGateway,
        settings: Settings,
        document_processor: RagDocumentProcessor | None = None,
        image_processor: ProfileImageProcessor | None = None,
    ) -> None:
        self.documents = documents
        self.chunks = chunks
        self.conversations = conversations
        self.search = search
        self.access = access
        self.users = users
        self.storage = storage
        self.llm = llm
        self.settings = settings
        self.document_processor = document_processor or RagDocumentProcessor()
        self.image_processor = image_processor or ProfileImageProcessor()

    async def upload_document(
        self,
        *,
        notebook_id: UUID,
        user_id: UUID,
        file: UploadFile,
        description: str | None = None,
    ) -> DocumentUploadResponse:
        await self._require_access(user_id=user_id, notebook_id=notebook_id)
        content, suffix, mime_type = await self.document_processor.read_upload(file)
        content_hash = self.document_processor.content_hash(content)
        existing = await self.documents.get_by_hash(
            notebook_id=str(notebook_id), content_hash=content_hash
        )
        if existing:
            chunk_count = await self._chunk_count(str(existing["document_id"]))
            return DocumentUploadResponse(data={**existing, "chunks_count": chunk_count})

        filename = file.filename or f"document{suffix}"
        storage_path = self.document_processor.storage_path(notebook_id, filename, suffix)
        text = self.document_processor.extract_text(content, suffix)
        chunks = self.document_processor.chunk_text(text)
        await self.storage.upload(
            bucket=self.settings.documents_bucket,
            path=storage_path,
            content=content,
            content_type=mime_type,
        )
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
        try:
            embeddings = await self._embed(chunks)
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
            document = await self._update_document_status(
                str(document["document_id"]), "completed"
            )
        except Exception:
            await self._update_document_status(str(document["document_id"]), "failed")
            raise
        return DocumentUploadResponse(data={**document, "chunks_count": len(chunks)})

    async def upload_profile_photo(
        self, *, user_id: UUID, file: UploadFile
    ) -> ProfilePhotoResponse:
        user = await self.users.get(UserRepositoryGetRequest(user_id=user_id))
        if user is None:
            raise ResourceNotFoundError()
        content, content_type = await self.image_processor.read_upload(file)
        path = self.image_processor.storage_path(user_id, content_type)
        await self.storage.upload(
            bucket=self.settings.profile_bucket,
            path=path,
            content=content,
            content_type=content_type,
        )
        data = await self.users.update(
            UserRepositoryUpdateRequest(
                user_id=user_id,
                payload=UserUpdate(
                    profile_image_path=path,
                    profile_image_mime_type=content_type,
                    profile_image_size_bytes=len(content),
                ),
                updated_at=datetime.now(UTC),
            )
        )
        if data is None:
            raise ResourceNotFoundError()
        return ProfilePhotoResponse(
            data={
                "user_id": data.get("user_id"),
                "profile_image_path": data.get("profile_image_path"),
                "profile_image_mime_type": data.get("profile_image_mime_type"),
                "profile_image_size_bytes": data.get("profile_image_size_bytes"),
            }
        )

    async def create_conversation(
        self, *, notebook_id: UUID, request: ConversationCreateRequest
    ) -> ConversationResponse:
        await self._require_access(user_id=request.user_id, notebook_id=notebook_id)
        data = await self.conversations.create(
            notebook_id=str(notebook_id),
            name=request.name,
        )
        return ConversationResponse(data=data)

    async def list_conversations(
        self, *, notebook_id: UUID, user_id: UUID, limit: int, offset: int
    ) -> ConversationListResponse:
        await self._require_access(user_id=user_id, notebook_id=notebook_id)
        data = await self.conversations.list_by_notebook(
            notebook_id=str(notebook_id), limit=limit, offset=offset
        )
        return ConversationListResponse(data=data, limit=limit, offset=offset)

    async def list_messages(
        self, *, conversation_id: UUID, user_id: UUID, limit: int, offset: int
    ) -> MessageListResponse:
        conversation = await self._get_conversation(conversation_id)
        await self._require_access(
            user_id=user_id, notebook_id=UUID(str(conversation["notebook_id"]))
        )
        data = await self.conversations.list_messages(
            conversation_id=str(conversation_id), limit=limit, offset=offset
        )
        return MessageListResponse(data=data, limit=limit, offset=offset)

    async def chat(self, *, conversation_id: UUID, request: ChatRequest) -> ChatResponse:
        conversation = await self._get_conversation(conversation_id)
        notebook_id = UUID(str(conversation["notebook_id"]))
        await self._require_access(user_id=request.user_id, notebook_id=notebook_id)

        order = await self.conversations.next_message_order(conversation_id=str(conversation_id))
        await self.conversations.create_message(
            conversation_id=str(conversation_id),
            role="user",
            content=request.content,
            order_message=order,
            sent_by_user_id=str(request.user_id),
        )

        query_embedding = await self._embed_one(request.content)
        sources = await self.search.search_chunks(
            notebook_id=str(notebook_id),
            embedding=query_embedding,
            limit=self.settings.rag_match_limit,
        )
        answer = await self._answer(request.content, sources, model=request.model)
        message = await self.conversations.create_message(
            conversation_id=str(conversation_id),
            role="assistant",
            content=answer,
            order_message=order + 1,
        )
        return ChatResponse(data=message, sources=sources)

    async def _require_access(self, *, user_id: UUID, notebook_id: UUID) -> None:
        allowed = await self.access.has_notebook_access(
            user_id=str(user_id), notebook_id=str(notebook_id)
        )
        if not allowed:
            raise ForbiddenError()

    async def _get_conversation(self, conversation_id: UUID) -> dict[str, Any]:
        conversation = await self.conversations.get(conversation_id=str(conversation_id))
        if conversation is None:
            raise ResourceNotFoundError()
        return conversation

    async def _update_document_status(self, document_id: str, status: str) -> dict[str, Any]:
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

    async def _chunk_count(self, document_id: str) -> int:
        return await self.chunks.count_for_document(document_id)

    async def _embed_one(self, text: str) -> list[float]:
        return (await self._embed([text]))[0]

    async def _embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            raise BadRequestError("No hay texto para vectorizar.")
        response = await self.llm.embeddings(
            model=self.settings.openrouter_embedding_model,
            input=list(texts),
        )
        data = self._response_data(response)
        embeddings = [item.get("embedding") for item in data if isinstance(item, Mapping)]
        if len(embeddings) != len(texts) or not all(isinstance(item, list) for item in embeddings):
            raise BadRequestError("Respuesta de embeddings invalida.")
        return [list(map(float, item)) for item in embeddings]

    async def _answer(self, question: str, sources: list[dict[str, Any]], model: str | None) -> str:
        context = "\n\n".join(
            f"[{index + 1}] {source.get('document_name')}: {source.get('content')}"
            for index, source in enumerate(sources)
        )
        messages: list[OpenRouterMessage] = [
            {
                "role": "system",
                "content": (
                    "Responde en espanol usando solo el contexto del notebook. "
                    "Si el contexto no contiene la respuesta, dilo claramente. "
                    "Cita fuentes como [1], [2] cuando uses fragmentos."
                ),
            },
            {
                "role": "user",
                "content": f"Contexto:\n{context or 'Sin contexto recuperado.'}\n\nPregunta:\n{question}",
            },
        ]
        response = await self.llm.chat_completion(
            model=model or self.settings.openrouter_chat_model,
            messages=messages,
            temperature=0.2,
        )
        if isinstance(response, list):
            raise BadRequestError("Streaming no soportado en este endpoint.")
        choices = response.get("choices")
        if not isinstance(choices, list) or not choices:
            raise BadRequestError("Respuesta del modelo invalida.")
        message = choices[0].get("message") if isinstance(choices[0], Mapping) else None
        content = message.get("content") if isinstance(message, Mapping) else None
        if not isinstance(content, str) or not content:
            raise BadRequestError("Respuesta del modelo sin contenido.")
        return content

    def _response_data(self, response: Mapping[str, Any]) -> list[Any]:
        data = response.get("data")
        if not isinstance(data, list):
            raise BadRequestError("Respuesta de embeddings invalida.")
        return data
