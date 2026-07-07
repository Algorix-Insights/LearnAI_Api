from app.infra.repositories.aggregate import BaseSupabaseAggregateRepository


class TagRepository(BaseSupabaseAggregateRepository):
    table_name = "tags"
    id_field = "id"
