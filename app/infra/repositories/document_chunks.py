from app.infra.repositories.aggregate import BaseSupabaseAggregateRepository


class DocumentChunkRepository(BaseSupabaseAggregateRepository):
    table_name = "document_chunks"
    id_field = "chunk_id"
