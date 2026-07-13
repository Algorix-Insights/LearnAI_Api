from __future__ import annotations

from uuid import UUID

from app.application.usecases.rag_support.common import RagAccessPolicy
from app.application.usecases.rag_support.llm import (
    MAX_CHAT_HISTORY_MESSAGES,
    RagLlmService,
)
from app.core.exceptions import ResourceNotFoundError
from app.domain.schemas.resources.rag import (
    ChatRequest,
    ChatResponse,
    ConversationCreateRequest,
    ConversationListResponse,
    ConversationResponse,
    MessageListResponse,
)
from app.infra.repositories.rag import ConversationRepository


class RagConversationWorkflow:
    """Handles notebook-scoped conversations, retrieval, and chat persistence."""

    def __init__(
        self,
        *,
        conversations: ConversationRepository,
        llm: RagLlmService,
        policy: RagAccessPolicy,
    ) -> None:
        self.conversations = conversations
        self.llm = llm
        self.policy = policy

    async def create_conversation(
        self,
        *,
        notebook_id: UUID,
        user_id: UUID,
        request: ConversationCreateRequest,
    ) -> ConversationResponse:
        await self.policy.require_access(user_id=user_id, notebook_id=notebook_id)
        data = await self.conversations.create(
            notebook_id=str(notebook_id),
            user_id=str(user_id),
            name=request.name,
        )
        return ConversationResponse(data=data)

    async def list_conversations(
        self, *, notebook_id: UUID, user_id: UUID, limit: int, offset: int
    ) -> ConversationListResponse:
        await self.policy.require_access(user_id=user_id, notebook_id=notebook_id)
        data = await self.conversations.list_by_notebook(
            notebook_id=str(notebook_id),
            user_id=str(user_id),
            limit=limit,
            offset=offset,
        )
        return ConversationListResponse(data=data, limit=limit, offset=offset)

    async def list_messages(
        self, *, conversation_id: UUID, user_id: UUID, limit: int, offset: int
    ) -> MessageListResponse:
        conversation = await self._get_conversation(conversation_id, user_id)
        await self.policy.require_access(
            user_id=user_id,
            notebook_id=UUID(str(conversation["notebook_id"])),
        )
        data = await self.conversations.list_messages(
            conversation_id=str(conversation_id), limit=limit, offset=offset
        )
        return MessageListResponse(data=data, limit=limit, offset=offset)

    async def chat(
        self, *, conversation_id: UUID, user_id: UUID, request: ChatRequest
    ) -> ChatResponse:
        conversation = await self._get_conversation(conversation_id, user_id)
        notebook_id = UUID(str(conversation["notebook_id"]))
        await self.policy.require_access(user_id=user_id, notebook_id=notebook_id)
        model = self.llm.resolve_model(request.model)
        await self.policy.reserve_ai_usage(user_id, "chat")

        await self.conversations.create_message(
            conversation_id=str(conversation_id),
            role="user",
            content=request.content,
            actor_id=str(user_id),
            sent_by_user_id=str(user_id),
        )

        query_embedding = await self.llm.embed_one(request.content)
        sources = await self.llm.search.search_chunks(
            notebook_id=str(notebook_id),
            embedding=query_embedding,
            limit=self.llm.match_limit(),
        )
        history = await self.conversations.list_recent_messages(
            conversation_id=str(conversation_id),
            limit=MAX_CHAT_HISTORY_MESSAGES,
        )
        answer = await self.llm.answer(
            request.content,
            sources,
            model=model,
            history=history,
        )
        message = await self.conversations.create_message(
            conversation_id=str(conversation_id),
            role="assistant",
            content=answer,
            actor_id=str(user_id),
        )
        return ChatResponse(data=message, sources=sources)

    async def _get_conversation(self, conversation_id: UUID, user_id: UUID) -> dict:
        conversation = await self.conversations.get(
            conversation_id=str(conversation_id),
            user_id=str(user_id),
        )
        if conversation is None:
            raise ResourceNotFoundError()
        return conversation
