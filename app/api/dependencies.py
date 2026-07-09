from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.application.usecases import (
    AttemptUseCase,
    AuthUseCase,
    DocumentChunkUseCase,
    DocumentUseCase,
    ExamUseCase,
    ExamQuestionUseCase,
    FlashcardUseCase,
    NotebookUseCase,
    NotebookTagUseCase,
    PersonalNotebookUseCase,
    QuestionOptionUseCase,
    QuestionUseCase,
    RoomMemberUseCase,
    RoomNotebookUseCase,
    RoomUseCase,
    StudyMemberUseCase,
    TagUseCase,
    UserAnswerUseCase,
    UserUseCase,
)
from app.core.exceptions import UnauthorizedError
from app.domain.schemas.resources.users import UserRead
from app.infra.repositories import (
    AttemptRepository,
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
    RoomNotebookRepository,
    RoomRepository,
    StudyMemberRepository,
    SupabaseAuthRepository,
    TagRepository,
    UserAnswerRepository,
    UserRepository,
)

bearer_scheme = HTTPBearer(auto_error=False)


def get_users_use_case() -> UserUseCase:
    return UserUseCase(UserRepository())


def get_notebooks_use_case() -> NotebookUseCase:
    return NotebookUseCase(NotebookRepository())


def get_rooms_use_case() -> RoomUseCase:
    return RoomUseCase(RoomRepository())


def get_study_members_use_case() -> StudyMemberUseCase:
    return StudyMemberUseCase(StudyMemberRepository())


def get_exams_use_case() -> ExamUseCase:
    return ExamUseCase(ExamRepository())


def get_questions_use_case() -> QuestionUseCase:
    return QuestionUseCase(QuestionRepository())


def get_question_options_use_case() -> QuestionOptionUseCase:
    return QuestionOptionUseCase(QuestionOptionRepository())


def get_attempts_use_case() -> AttemptUseCase:
    return AttemptUseCase(AttemptRepository())


def get_user_answers_use_case() -> UserAnswerUseCase:
    return UserAnswerUseCase(UserAnswerRepository())


def get_flashcards_use_case() -> FlashcardUseCase:
    return FlashcardUseCase(FlashcardRepository())


def get_documents_use_case() -> DocumentUseCase:
    return DocumentUseCase(DocumentRepository())


def get_document_chunks_use_case() -> DocumentChunkUseCase:
    return DocumentChunkUseCase(DocumentChunkRepository())


def get_tags_use_case() -> TagUseCase:
    return TagUseCase(TagRepository())


def get_notebook_tags_use_case() -> NotebookTagUseCase:
    return NotebookTagUseCase(NotebookTagRepository())


def get_room_members_use_case() -> RoomMemberUseCase:
    return RoomMemberUseCase(MemberRoomRepository())


def get_exam_questions_use_case() -> ExamQuestionUseCase:
    return ExamQuestionUseCase(ExamQuestionRepository())


def get_personal_notebooks_use_case() -> PersonalNotebookUseCase:
    return PersonalNotebookUseCase(PersonalNotebookRepository())


def get_room_notebooks_use_case() -> RoomNotebookUseCase:
    return RoomNotebookUseCase(RoomNotebookRepository())


def get_auth_use_case() -> AuthUseCase:
    return AuthUseCase(SupabaseAuthRepository(), UserRepository())


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    auth_use_case: Annotated[AuthUseCase, Depends(get_auth_use_case)],
) -> UserRead:
    if not credentials or not credentials.credentials:
        raise UnauthorizedError("No autorizado. Se requiere header Authorization: Bearer <token>.")
    return await auth_use_case.get_current_user_profile(credentials.credentials)

