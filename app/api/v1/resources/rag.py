from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status

from app.api.dependencies import get_rag_use_case
from app.application.usecases import RagUseCase
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

router = APIRouter(tags=["rag"])


@router.post(
    "/notebooks/{notebook_id}/documents/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["documents"],
)
async def upload_notebook_document(
    notebook_id: UUID,
    user_id: Annotated[UUID, Form()],
    file: Annotated[UploadFile, File()],
    use_case: Annotated[RagUseCase, Depends(get_rag_use_case)],
    description: Annotated[str | None, Form()] = None,
) -> DocumentUploadResponse:
    return await use_case.upload_document(
        notebook_id=notebook_id,
        user_id=user_id,
        file=file,
        description=description,
    )


@router.post(
    "/users/{user_id}/profile-photo",
    response_model=ProfilePhotoResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["users"],
)
async def upload_profile_photo(
    user_id: UUID,
    file: Annotated[UploadFile, File()],
    use_case: Annotated[RagUseCase, Depends(get_rag_use_case)],
) -> ProfilePhotoResponse:
    return await use_case.upload_profile_photo(user_id=user_id, file=file)


@router.post(
    "/notebooks/{notebook_id}/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["conversations"],
)
async def create_notebook_conversation(
    notebook_id: UUID,
    payload: ConversationCreateRequest,
    use_case: Annotated[RagUseCase, Depends(get_rag_use_case)],
) -> ConversationResponse:
    return await use_case.create_conversation(notebook_id=notebook_id, request=payload)


@router.get(
    "/notebooks/{notebook_id}/conversations",
    response_model=ConversationListResponse,
    tags=["conversations"],
)
async def list_notebook_conversations(
    notebook_id: UUID,
    user_id: Annotated[UUID, Query()],
    use_case: Annotated[RagUseCase, Depends(get_rag_use_case)],
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ConversationListResponse:
    return await use_case.list_conversations(
        notebook_id=notebook_id,
        user_id=user_id,
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
    user_id: Annotated[UUID, Query()],
    use_case: Annotated[RagUseCase, Depends(get_rag_use_case)],
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> MessageListResponse:
    return await use_case.list_messages(
        conversation_id=conversation_id,
        user_id=user_id,
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
    use_case: Annotated[RagUseCase, Depends(get_rag_use_case)],
) -> ChatResponse:
    return await use_case.chat(conversation_id=conversation_id, request=payload)
