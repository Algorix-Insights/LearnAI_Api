from app.infra.repositories.aggregate import BaseSupabaseAggregateRepository


class UserAnswerRepository(BaseSupabaseAggregateRepository):
    table_name = "user_answers"
    id_field = "answer_id"
