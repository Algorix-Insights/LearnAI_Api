from app.infra.repositories.aggregate import BaseSupabaseAggregateRepository


class AttemptRepository(BaseSupabaseAggregateRepository):
    table_name = "attempts"
    id_field = "attempt_id"
