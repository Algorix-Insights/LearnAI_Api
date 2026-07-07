from app.infra.repositories.aggregate import BaseSupabaseAggregateRepository


class FlashcardRepository(BaseSupabaseAggregateRepository):
    table_name = "flashcards"
    id_field = "flashcard_id"
