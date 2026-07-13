from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status

from app.api.dependencies import get_current_user, get_rag_use_case
from app.application.usecases import RagUseCase
from app.core.exceptions import UnauthorizedError
from app.domain.schemas.resources.rag import (
    ChatRequest,
    ChatResponse,
    ConversationCreateRequest,
    ConversationListResponse,
    ConversationResponse,
    DocumentUploadResponse,
    ExamGenerationRequest,
    ExamGenerationResponse,
    FlashcardGenerationRequest,
    FlashcardGenerationResponse,
    MessageListResponse,
)
from app.domain.schemas.resources.documents import DocumentResponse
from app.domain.schemas.resources.users import UserRead

router = APIRouter(tags=["rag"])


@router.post(
    "/notebooks/{notebook_id}/documents/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["documents"],
)
async def upload_notebook_document(
    notebook_id: UUID,
    file: Annotated[UploadFile, File()],
    current_user: Annotated[UserRead, Depends(get_current_user)],
    use_case: Annotated[RagUseCase, Depends(get_rag_use_case)],
    description: Annotated[str | None, Form(max_length=1000)] = None,
) -> DocumentUploadResponse:
    return await use_case.upload_document(
        notebook_id=notebook_id,
        user_id=_actor_id(current_user),
        file=file,
        description=description,
    )


@router.delete(
    "/notebooks/{notebook_id}/documents/{document_id}",
    response_model=DocumentResponse,
    tags=["documents"],
)
async def delete_notebook_document(
    notebook_id: UUID,
    document_id: UUID,
    current_user: Annotated[UserRead, Depends(get_current_user)],
    use_case: Annotated[RagUseCase, Depends(get_rag_use_case)],
) -> DocumentResponse:
    return await use_case.delete_document(
        notebook_id=notebook_id,
        document_id=document_id,
        user_id=_actor_id(current_user),
    )


@router.post(
    "/notebooks/{notebook_id}/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["conversations"],
)
async def create_notebook_conversation(
    notebook_id: UUID,
    payload: ConversationCreateRequest,
    current_user: Annotated[UserRead, Depends(get_current_user)],
    use_case: Annotated[RagUseCase, Depends(get_rag_use_case)],
) -> ConversationResponse:
    return await use_case.create_conversation(
        notebook_id=notebook_id,
        user_id=_actor_id(current_user),
        request=payload,
    )


@router.get(
    "/notebooks/{notebook_id}/conversations",
    response_model=ConversationListResponse,
    tags=["conversations"],
)
async def list_notebook_conversations(
    notebook_id: UUID,
    current_user: Annotated[UserRead, Depends(get_current_user)],
    use_case: Annotated[RagUseCase, Depends(get_rag_use_case)],
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ConversationListResponse:
    return await use_case.list_conversations(
        notebook_id=notebook_id,
        user_id=_actor_id(current_user),
        limit=limit,
        offset=offset,
    )


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=MessageListResponse,
    tags=["conversations"],
)
async def list_conversation_messages(
    conversation_id: UUID,
    current_user: Annotated[UserRead, Depends(get_current_user)],
    use_case: Annotated[RagUseCase, Depends(get_rag_use_case)],
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> MessageListResponse:
    return await use_case.list_messages(
        conversation_id=conversation_id,
        user_id=_actor_id(current_user),
        limit=limit,
        offset=offset,
    )


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=ChatResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["conversations"],
)
async def chat_with_notebook(
    conversation_id: UUID,
    payload: ChatRequest,
    current_user: Annotated[UserRead, Depends(get_current_user)],
    use_case: Annotated[RagUseCase, Depends(get_rag_use_case)],
) -> ChatResponse:
    return await use_case.chat(
        conversation_id=conversation_id,
        user_id=_actor_id(current_user),
        request=payload,
    )


@router.post(
    "/notebooks/{notebook_id}/flashcards/generate",
    response_model=FlashcardGenerationResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["flashcards"],
)
async def generate_notebook_flashcards(
    notebook_id: UUID,
    payload: FlashcardGenerationRequest,
    current_user: Annotated[UserRead, Depends(get_current_user)],
    use_case: Annotated[RagUseCase, Depends(get_rag_use_case)],
) -> FlashcardGenerationResponse:
    return await use_case.generate_flashcards(
        notebook_id=notebook_id,
        user_id=_actor_id(current_user),
        request=payload,
    )


@router.post(
    "/notebooks/{notebook_id}/exams/generate",
    response_model=ExamGenerationResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["exams"],
)
async def generate_notebook_exam(
    notebook_id: UUID,
    payload: ExamGenerationRequest,
    current_user: Annotated[UserRead, Depends(get_current_user)],
    use_case: Annotated[RagUseCase, Depends(get_rag_use_case)],
) -> ExamGenerationResponse:
    return await use_case.generate_exam(
        notebook_id=notebook_id,
        user_id=_actor_id(current_user),
        request=payload,
    )


def _actor_id(current_user: UserRead) -> UUID:
    if current_user.user_id is None:
        raise UnauthorizedError()
    return current_user.user_id
