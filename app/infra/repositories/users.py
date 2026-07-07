from app.infra.repositories.aggregate import (
    BaseSupabaseAggregateRepository,
    BaseSupabaseCompositeRepository,
)


class UserRepository(BaseSupabaseAggregateRepository):
    table_name = "users"
    id_field = "user_id"


class PersonalNotebookRepository(BaseSupabaseCompositeRepository):
    table_name = "personal_notebooks"
