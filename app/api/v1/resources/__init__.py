from app.api.v1.resources.attempts import router as attempts_router
from app.api.v1.resources.auth import router as auth_router
from app.api.v1.resources.document_chunks import router as document_chunks_router
from app.api.v1.resources.documents import router as documents_router
from app.api.v1.resources.exams import router as exams_router
from app.api.v1.resources.flashcards import router as flashcards_router
from app.api.v1.resources.notebooks import router as notebooks_router
from app.api.v1.resources.question_options import router as question_options_router
from app.api.v1.resources.questions import router as questions_router
from app.api.v1.resources.rooms import router as rooms_router
from app.api.v1.resources.study_members import router as study_members_router
from app.api.v1.resources.tags import router as tags_router
from app.api.v1.resources.user_answers import router as user_answers_router
from app.api.v1.resources.users import router as users_router

RESOURCE_ROUTERS = [
    auth_router,
    users_router,
    notebooks_router,
    rooms_router,
    study_members_router,
    exams_router,
    questions_router,
    question_options_router,
    attempts_router,
    user_answers_router,
    flashcards_router,
    documents_router,
    document_chunks_router,
    tags_router,
]
