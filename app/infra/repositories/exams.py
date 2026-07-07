from app.infra.repositories.aggregate import (
    BaseSupabaseAggregateRepository,
    BaseSupabaseCompositeRepository,
)


class ExamRepository(BaseSupabaseAggregateRepository):
    table_name = "exams"
    id_field = "exam_id"


class ExamQuestionRepository(BaseSupabaseCompositeRepository):
    table_name = "exam_questions"
