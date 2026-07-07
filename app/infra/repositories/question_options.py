from app.infra.repositories.aggregate import BaseSupabaseAggregateRepository


class QuestionOptionRepository(BaseSupabaseAggregateRepository):
    table_name = "questions_options"
    id_field = "option_id"
