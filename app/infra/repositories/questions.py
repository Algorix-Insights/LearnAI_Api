from app.infra.repositories.aggregate import BaseSupabaseAggregateRepository


class QuestionRepository(BaseSupabaseAggregateRepository):
    table_name = "questions"
    id_field = "question_id"
