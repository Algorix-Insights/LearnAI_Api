from typing import Any, get_type_hints

from app.infra.repositories.attempts import AttemptRepository


def test_attempt_repository_annotations_are_safe_on_python_312() -> None:
    """Force Python 3.14 to expose annotation errors raised eagerly on 3.12."""
    hints = get_type_hints(AttemptRepository.list_exam_questions)

    assert hints["return"] == list[dict[str, Any]]
