from app.infra.repositories.aggregate import (
    BaseSupabaseAggregateRepository,
    BaseSupabaseCompositeRepository,
)


class NotebookRepository(BaseSupabaseAggregateRepository):
    table_name = "notebooks"
    id_field = "notebook_id"


class NotebookTagRepository(BaseSupabaseCompositeRepository):
    table_name = "notebook_tags"
