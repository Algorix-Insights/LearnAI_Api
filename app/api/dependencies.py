import logging
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import Client

from app.application.usecases import (
    AttemptUseCase,
    AuthUseCase,
    DocumentChunkUseCase,
    DocumentUseCase,
    ExamQuestionUseCase,
    ExamUseCase,
    FlashcardUseCase,
    NotebookTagUseCase,
    NotebookUseCase,
    PersonalNotebookUseCase,
    QuestionOptionUseCase,
    QuestionUseCase,
    RagUseCase,
    RoomMemberUseCase,
    RoomNotebookUseCase,
    RoomUseCase,
    StudyMemberUseCase,
    TagUseCase,
    UserAnswerUseCase,
    UserUseCase,
)
from app.application.usecases.exam_attempts import ExamAttemptWorkflowUseCase
from app.application.usecases.user_profile import UserProfileUseCase
from app.application.usecases.user_statistics import UserStatisticsUseCase
from app.core.config import Settings, get_settings
from app.core.exceptions import AuthUnavailableError, UnauthorizedError
from app.domain.schemas.resources.users import UserRead
from app.infra.agents.answer_verifier import OpenRouterAnswerVerifier
from app.infra.clients import OpenRouterClient
from app.infra.db.supabase import (
    create_supabase_user_client,
    get_supabase_admin_client,
)
from app.infra.repositories import (
    AttemptRepository,
    AiUsageRepository,
    DocumentChunkRepository,
    DocumentRepository,
    ExamQuestionRepository,
    ExamRepository,
    FlashcardRepository,
    MemberRoomRepository,
    NotebookRepository,
    NotebookTagRepository,
    PersonalNotebookRepository,
    QuestionOptionRepository,
    QuestionRepository,
    RagGenerationRepository,
    RoomNotebookRepository,
    RoomRepository,
    StudyMemberRepository,
    SupabaseAuthRepository,
    TagRepository,
    UserAnswerRepository,
    UserRepository,
)
from app.infra.repositories.rag import (
    ConversationRepository,
    NotebookAccessRepository,
    RagSearchRepository,
)
from app.infra.repositories.user_statistics import UserStatisticsRepository
from app.infra.storage import SupabaseStorage

bearer_scheme = HTTPBearer(auto_error=False)
logger = logging.getLogger("learnia.auth")


def _ai_usage_repository(client: Client, settings: Settings) -> AiUsageRepository | None:
    if not settings.ai_usage_quota_enabled:
        return None
    return AiUsageRepository(client)


def get_user_data_client(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
    ],
) -> Client:
    """Request-scoped data client; its JWT is what PostgreSQL RLS evaluates."""
    if not credentials or not credentials.credentials:
        raise UnauthorizedError()
    return create_supabase_user_client(credentials.credentials)


def get_users_use_case(
    client: Annotated[Client, Depends(get_user_data_client)],
) -> UserUseCase:
    return UserUseCase(UserRepository(client))


def get_notebooks_use_case(
    client: Annotated[Client, Depends(get_user_data_client)],
) -> NotebookUseCase:
    return NotebookUseCase(NotebookRepository(client))


def get_rooms_use_case(
    client: Annotated[Client, Depends(get_user_data_client)],
) -> RoomUseCase:
    return RoomUseCase(RoomRepository(client))


def get_study_members_use_case(
    client: Annotated[Client, Depends(get_user_data_client)],
) -> StudyMemberUseCase:
    return StudyMemberUseCase(StudyMemberRepository(client))


def get_exams_use_case(
    client: Annotated[Client, Depends(get_user_data_client)],
) -> ExamUseCase:
    return ExamUseCase(ExamRepository(client))


def get_questions_use_case(
    client: Annotated[Client, Depends(get_user_data_client)],
) -> QuestionUseCase:
    return QuestionUseCase(QuestionRepository(client))


def get_question_options_use_case(
    client: Annotated[Client, Depends(get_user_data_client)],
) -> QuestionOptionUseCase:
    return QuestionOptionUseCase(QuestionOptionRepository(client))


def get_attempts_use_case(
    client: Annotated[Client, Depends(get_user_data_client)],
) -> AttemptUseCase:
    return AttemptUseCase(AttemptRepository(client))


def get_exam_attempt_workflow_use_case() -> ExamAttemptWorkflowUseCase:
    # RPCs are service-only. Actor identity is derived from the verified JWT and
    # checked again inside the use case/RPC before every read or mutation.
    settings = get_settings()
    admin = get_supabase_admin_client()
    verifier = None
    if settings.openrouter_api_key:
        verifier = OpenRouterAnswerVerifier(
            _openrouter_client(), model=settings.openrouter_chat_model
        )
    return ExamAttemptWorkflowUseCase(
        AttemptRepository(admin),
        open_answer_verifier=verifier,
        usage=_ai_usage_repository(admin, settings),
    )


def get_user_answers_use_case(
    client: Annotated[Client, Depends(get_user_data_client)],
) -> UserAnswerUseCase:
    return UserAnswerUseCase(UserAnswerRepository(client))


def get_flashcards_use_case(
    client: Annotated[Client, Depends(get_user_data_client)],
) -> FlashcardUseCase:
    return FlashcardUseCase(FlashcardRepository(client))


def get_documents_use_case(
    client: Annotated[Client, Depends(get_user_data_client)],
) -> DocumentUseCase:
    return DocumentUseCase(DocumentRepository(client))


def get_document_chunks_use_case(
    client: Annotated[Client, Depends(get_user_data_client)],
) -> DocumentChunkUseCase:
    return DocumentChunkUseCase(DocumentChunkRepository(client))


def get_tags_use_case(
    client: Annotated[Client, Depends(get_user_data_client)],
) -> TagUseCase:
    return TagUseCase(TagRepository(client))


def get_notebook_tags_use_case(
    client: Annotated[Client, Depends(get_user_data_client)],
) -> NotebookTagUseCase:
    return NotebookTagUseCase(NotebookTagRepository(client))


def get_room_members_use_case(
    client: Annotated[Client, Depends(get_user_data_client)],
) -> RoomMemberUseCase:
    return RoomMemberUseCase(MemberRoomRepository(client))


def get_exam_questions_use_case(
    client: Annotated[Client, Depends(get_user_data_client)],
) -> ExamQuestionUseCase:
    return ExamQuestionUseCase(ExamQuestionRepository(client))


def get_personal_notebooks_use_case(
    client: Annotated[Client, Depends(get_user_data_client)],
) -> PersonalNotebookUseCase:
    return PersonalNotebookUseCase(PersonalNotebookRepository(client))


def get_room_notebooks_use_case(
    client: Annotated[Client, Depends(get_user_data_client)],
) -> RoomNotebookUseCase:
    return RoomNotebookUseCase(RoomNotebookRepository(client))


def get_user_profile_use_case(
    client: Annotated[Client, Depends(get_user_data_client)],
) -> UserProfileUseCase:
    return UserProfileUseCase(
        UserRepository(client),
        SupabaseStorage(client),
        get_settings(),
    )


def get_user_statistics_use_case(
    client: Annotated[Client, Depends(get_user_data_client)],
) -> UserStatisticsUseCase:
    return UserStatisticsUseCase(UserStatisticsRepository(client))


def get_auth_use_case() -> AuthUseCase:
    try:
        return AuthUseCase(
            SupabaseAuthRepository(),
            UserRepository(get_supabase_admin_client()),
        )
    except Exception as exc:
        logger.exception("auth_client_initialization_failed")
        raise AuthUnavailableError() from exc


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
    ],
    auth_use_case: Annotated[AuthUseCase, Depends(get_auth_use_case)],
) -> UserRead:
    if not credentials or not credentials.credentials:
        raise UnauthorizedError(
            "No autorizado. Se requiere header Authorization: Bearer <token>."
        )
    return await auth_use_case.get_current_user_profile(credentials.credentials)


def get_rag_use_case() -> RagUseCase:
    # Generation spans multiple internal tables and currently uses service-only
    # repositories. Every public method first checks the JWT-derived actor against
    # notebook ownership/membership; generic CRUD uses request-scoped RLS clients.
    settings = get_settings()
    admin = get_supabase_admin_client()
    return RagUseCase(
        documents=DocumentRepository(admin),
        chunks=DocumentChunkRepository(admin),
        conversations=ConversationRepository(admin),
        exams=ExamRepository(admin),
        exam_questions=ExamQuestionRepository(admin),
        questions=QuestionRepository(admin),
        question_options=QuestionOptionRepository(admin),
        flashcards=FlashcardRepository(admin),
        search=RagSearchRepository(admin),
        access=NotebookAccessRepository(admin),
        storage=SupabaseStorage(admin),
        llm=_openrouter_client(),
        settings=settings,
        generation=RagGenerationRepository(admin),
        usage=_ai_usage_repository(admin, settings),
    )


def _openrouter_client() -> OpenRouterClient:
    settings = get_settings()
    return OpenRouterClient(
        settings.openrouter_api_key or "",
        http_referer=settings.openrouter_http_referer,
        app_title=settings.openrouter_app_title,
        app_categories=settings.openrouter_app_categories,
    )
