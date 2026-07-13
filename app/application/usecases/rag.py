from __future__ import annotations

from uuid import UUID

from fastapi import UploadFile

from app.application.interfaces import OpenRouterGateway
from app.application.usecases.rag_support import (
    RagAccessPolicy,
    RagConversationWorkflow,
    RagDocumentWorkflow,
    RagLlmService,
    RagStudyMaterialWorkflow,
)
from app.core.config import Settings
from app.domain.schemas.resources.documents import DocumentResponse
from app.domain.schemas.resources import rag as rag_schemas
from app.domain.services.rag import RagDocumentProcessor
from app.infra.repositories.ai_usage import AiUsageRepository
from app.infra.repositories.document_chunks import DocumentChunkRepository
from app.infra.repositories.documents import DocumentRepository
from app.infra.repositories.exams import ExamQuestionRepository, ExamRepository
from app.infra.repositories.flashcards import FlashcardRepository
from app.infra.repositories.question_options import QuestionOptionRepository
from app.infra.repositories.questions import QuestionRepository
from app.infra.repositories.rag import (
    ConversationRepository,
    NotebookAccessRepository,
    RagSearchRepository,
)
from app.infra.repositories.rag_generation import RagGenerationRepository
from app.infra.storage import SupabaseStorage


class RagUseCase:
    """Stable RAG facade that delegates each workflow to a focused collaborator."""

    def __init__(
        self,
        *,
        documents: DocumentRepository,
        chunks: DocumentChunkRepository,
        conversations: ConversationRepository,
        exams: ExamRepository,
        exam_questions: ExamQuestionRepository,
        questions: QuestionRepository,
        question_options: QuestionOptionRepository,
        flashcards: FlashcardRepository,
        search: RagSearchRepository,
        access: NotebookAccessRepository,
        storage: SupabaseStorage,
        llm: OpenRouterGateway,
        settings: Settings,
        generation: RagGenerationRepository | None = None,
        usage: AiUsageRepository | None = None,
        document_processor: RagDocumentProcessor | None = None,
    ) -> None:
        # Keep the original dependency attributes public for backwards compatibility.
        self.documents = documents
        self.chunks = chunks
        self.conversations = conversations
        self.exams = exams
        self.exam_questions = exam_questions
        self.questions = questions
        self.question_options = question_options
        self.flashcards = flashcards
        self.search = search
        self.access = access
        self.storage = storage
        self.llm = llm
        self.settings = settings
        self.generation = generation
        self.usage = usage
        self.document_processor = document_processor or RagDocumentProcessor()

        policy = RagAccessPolicy(
            access=access,
            usage=usage,
            generation=generation,
        )
        llm_service = RagLlmService(llm=llm, search=search, settings=settings)
        self._documents = RagDocumentWorkflow(
            documents=documents,
            chunks=chunks,
            storage=storage,
            settings=settings,
            document_processor=self.document_processor,
            llm=llm_service,
            policy=policy,
        )
        self._conversations = RagConversationWorkflow(
            conversations=conversations,
            llm=llm_service,
            policy=policy,
        )
        self._study_materials = RagStudyMaterialWorkflow(
            exams=exams,
            exam_questions=exam_questions,
            questions=questions,
            question_options=question_options,
            flashcards=flashcards,
            generation=generation,
            llm=llm_service,
            policy=policy,
        )

    async def upload_document(
        self,
        *,
        notebook_id: UUID,
        user_id: UUID,
        file: UploadFile,
        description: str | None = None,
    ) -> rag_schemas.DocumentUploadResponse:
        return await self._documents.upload_document(
            notebook_id=notebook_id,
            user_id=user_id,
            file=file,
            description=description,
        )

    async def delete_document(
        self, *, notebook_id: UUID, document_id: UUID, user_id: UUID
    ) -> DocumentResponse:
        return await self._documents.delete_document(
            notebook_id=notebook_id,
            document_id=document_id,
            user_id=user_id,
        )

    async def create_conversation(
        self,
        *,
        notebook_id: UUID,
        user_id: UUID,
        request: rag_schemas.ConversationCreateRequest,
    ) -> rag_schemas.ConversationResponse:
        return await self._conversations.create_conversation(
            notebook_id=notebook_id, user_id=user_id, request=request
        )

    async def list_conversations(
        self, *, notebook_id: UUID, user_id: UUID, limit: int, offset: int
    ) -> rag_schemas.ConversationListResponse:
        return await self._conversations.list_conversations(
            notebook_id=notebook_id,
            user_id=user_id,
            limit=limit,
            offset=offset,
        )

    async def list_messages(
        self, *, conversation_id: UUID, user_id: UUID, limit: int, offset: int
    ) -> rag_schemas.MessageListResponse:
        return await self._conversations.list_messages(
            conversation_id=conversation_id,
            user_id=user_id,
            limit=limit,
            offset=offset,
        )

    async def chat(
        self,
        *,
        conversation_id: UUID,
        user_id: UUID,
        request: rag_schemas.ChatRequest,
    ) -> rag_schemas.ChatResponse:
        return await self._conversations.chat(
            conversation_id=conversation_id, user_id=user_id, request=request
        )

    async def generate_flashcards(
        self,
        *,
        notebook_id: UUID,
        user_id: UUID,
        request: rag_schemas.FlashcardGenerationRequest,
    ) -> rag_schemas.FlashcardGenerationResponse:
        return await self._study_materials.generate_flashcards(
            notebook_id=notebook_id, user_id=user_id, request=request
        )

    async def list_flashcards(
        self, *, notebook_id: UUID, user_id: UUID, limit: int, offset: int
    ) -> rag_schemas.FlashcardStudyListResponse:
        return await self._study_materials.list_flashcards(
            notebook_id=notebook_id,
            user_id=user_id,
            limit=limit,
            offset=offset,
        )

    async def generate_exam(
        self,
        *,
        notebook_id: UUID,
        user_id: UUID,
        request: rag_schemas.ExamGenerationRequest,
    ) -> rag_schemas.ExamGenerationResponse:
        return await self._study_materials.generate_exam(
            notebook_id=notebook_id, user_id=user_id, request=request
        )
