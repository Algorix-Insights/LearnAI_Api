from app.domain.interfaces.attempts import AttemptRepository, ExamAttemptWorkflowRepository
from app.domain.interfaces.auth import AuthRepository
from app.domain.interfaces.document_chunks import DocumentChunkRepository
from app.domain.interfaces.documents import DocumentRepository
from app.domain.interfaces.exams import ExamQuestionRepository, ExamRepository
from app.domain.interfaces.flashcards import FlashcardRepository
from app.domain.interfaces.notebooks import NotebookRepository, NotebookTagRepository
from app.domain.interfaces.question_options import QuestionOptionRepository
from app.domain.interfaces.questions import QuestionRepository
from app.domain.interfaces.rooms import RoomMemberRepository, RoomNotebookRepository, RoomRepository
from app.domain.interfaces.study_members import StudyMemberRepository
from app.domain.interfaces.tags import TagRepository
from app.domain.interfaces.user_answers import UserAnswerRepository
from app.domain.interfaces.users import PersonalNotebookRepository, UserRepository
from app.domain.interfaces.user_statistics import UserStatisticsRepository

__all__ = [
    "AttemptRepository",
    "ExamAttemptWorkflowRepository",
    "AuthRepository",
    "DocumentChunkRepository",
    "DocumentRepository",
    "ExamQuestionRepository",
    "ExamRepository",
    "FlashcardRepository",
    "NotebookRepository",
    "NotebookTagRepository",
    "PersonalNotebookRepository",
    "QuestionOptionRepository",
    "QuestionRepository",
    "RoomMemberRepository",
    "RoomNotebookRepository",
    "RoomRepository",
    "StudyMemberRepository",
    "TagRepository",
    "UserAnswerRepository",
    "UserRepository",
    "UserStatisticsRepository",
]
