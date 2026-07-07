from app.infra.repositories.aggregate import BaseSupabaseAggregateRepository


class DocumentRepository(BaseSupabaseAggregateRepository):
    table_name = "documents"
    id_field = "document_id"
