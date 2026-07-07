from app.application.usecases.aggregate_crud import AggregateCrudUseCase
from app.domain.aggregates import AGGREGATES
from app.domain.interfaces import AggregateRepository


class FlashcardUseCase(AggregateCrudUseCase):
    def __init__(self, repository: AggregateRepository) -> None:
        super().__init__(AGGREGATES["flashcards"], repository)
