from pydantic import BaseModel, ConfigDict

from app.domain.schemas import entities


class AggregateDefinition(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    name: str
    route_prefix: str
    table_name: str
    id_field: str
    create_schema: type[BaseModel]
    update_schema: type[BaseModel]
    hidden_fields: tuple[str, ...] = ()
    updated_at_field: str | None = "updated_at"


AGGREGATES: dict[str, AggregateDefinition] = {
    "users": AggregateDefinition(
        name="users",
        route_prefix="/users",
        table_name="users",
        id_field="user_id",
        create_schema=entities.UserCreate,
        update_schema=entities.UserUpdate,
        hidden_fields=("hash_password",),
    ),
    "notebooks": AggregateDefinition(
        name="notebooks",
        route_prefix="/notebooks",
        table_name="notebooks",
        id_field="notebook_id",
        create_schema=entities.NotebookCreate,
        update_schema=entities.NotebookUpdate,
    ),
    "rooms": AggregateDefinition(
        name="rooms",
        route_prefix="/rooms",
        table_name="rooms",
        id_field="room_id",
        create_schema=entities.RoomCreate,
        update_schema=entities.RoomUpdate,
    ),
    "study-members": AggregateDefinition(
        name="study-members",
        route_prefix="/study-members",
        table_name="study_members",
        id_field="member_id",
        create_schema=entities.StudyMemberCreate,
        update_schema=entities.StudyMemberUpdate,
    ),
    "exams": AggregateDefinition(
        name="exams",
        route_prefix="/exams",
        table_name="exams",
        id_field="exam_id",
        create_schema=entities.ExamCreate,
        update_schema=entities.ExamUpdate,
    ),
    "questions": AggregateDefinition(
        name="questions",
        route_prefix="/questions",
        table_name="questions",
        id_field="question_id",
        create_schema=entities.QuestionCreate,
        update_schema=entities.QuestionUpdate,
        updated_at_field=None,
    ),
    "question-options": AggregateDefinition(
        name="question-options",
        route_prefix="/question-options",
        table_name="questions_options",
        id_field="option_id",
        create_schema=entities.QuestionOptionCreate,
        update_schema=entities.QuestionOptionUpdate,
        updated_at_field=None,
    ),
    "attempts": AggregateDefinition(
        name="attempts",
        route_prefix="/attempts",
        table_name="attempts",
        id_field="attempt_id",
        create_schema=entities.AttemptCreate,
        update_schema=entities.AttemptUpdate,
        updated_at_field=None,
    ),
    "user-answers": AggregateDefinition(
        name="user-answers",
        route_prefix="/user-answers",
        table_name="user_answers",
        id_field="answer_id",
        create_schema=entities.UserAnswerCreate,
        update_schema=entities.UserAnswerUpdate,
        updated_at_field=None,
    ),
    "flashcards": AggregateDefinition(
        name="flashcards",
        route_prefix="/flashcards",
        table_name="flashcards",
        id_field="flashcard_id",
        create_schema=entities.FlashcardCreate,
        update_schema=entities.FlashcardUpdate,
        updated_at_field=None,
    ),
    "documents": AggregateDefinition(
        name="documents",
        route_prefix="/documents",
        table_name="documents",
        id_field="document_id",
        create_schema=entities.DocumentCreate,
        update_schema=entities.DocumentUpdate,
    ),
    "document-chunks": AggregateDefinition(
        name="document-chunks",
        route_prefix="/document-chunks",
        table_name="document_chunks",
        id_field="chunk_id",
        create_schema=entities.DocumentChunkCreate,
        update_schema=entities.DocumentChunkUpdate,
        updated_at_field=None,
    ),
    "tags": AggregateDefinition(
        name="tags",
        route_prefix="/tags",
        table_name="tags",
        id_field="id",
        create_schema=entities.TagCreate,
        update_schema=entities.TagUpdate,
        updated_at_field=None,
    ),
}
