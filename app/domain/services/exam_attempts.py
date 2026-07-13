from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Mapping
import unicodedata


@dataclass(frozen=True)
class ExamAttemptGrade:
    grades: list[dict[str, Any]]
    earned_points: Decimal
    total_points: Decimal
    score: Decimal
    answered_questions: int
    total_questions: int


class ExamAttemptGrader:
    """Pure deterministic grader. Correct answers never leave this service."""

    _percentage = Decimal("100")
    _two_decimals = Decimal("0.01")

    def grade(
        self,
        *,
        questions: list[dict[str, Any]],
        answers: list[dict[str, Any]],
        open_answer_correctness: Mapping[str, bool] | None = None,
    ) -> ExamAttemptGrade:
        answers_by_question = {
            str(answer["question_id"]): answer
            for answer in answers
            if answer.get("question_id") is not None
        }
        grades: list[dict[str, Any]] = []
        earned_points = Decimal("0")
        total_points = Decimal("0")
        answered_questions = 0

        for question in questions:
            points = self._as_decimal(question.get("points", 0))
            total_points += points
            answer = answers_by_question.get(str(question.get("question_id")))
            if answer is None:
                continue

            answered_questions += 1
            is_correct = self._is_correct(
                question=question,
                answer=answer,
                open_answer_correctness=open_answer_correctness or {},
            )
            awarded = points if is_correct else Decimal("0")
            earned_points += awarded
            if answer.get("answer_id") is not None:
                grades.append(
                    {
                        "answer_id": str(answer["answer_id"]),
                        "is_correct": is_correct,
                        "points_awarded": str(awarded.quantize(self._two_decimals)),
                    }
                )

        score = Decimal("0")
        if total_points > 0:
            score = (earned_points / total_points * self._percentage).quantize(
                self._two_decimals,
                rounding=ROUND_HALF_UP,
            )

        return ExamAttemptGrade(
            grades=grades,
            earned_points=earned_points.quantize(self._two_decimals),
            total_points=total_points.quantize(self._two_decimals),
            score=score,
            answered_questions=answered_questions,
            total_questions=len(questions),
        )

    def _is_correct(
        self,
        *,
        question: dict[str, Any],
        answer: dict[str, Any],
        open_answer_correctness: Mapping[str, bool],
    ) -> bool:
        if question.get("type") == "open":
            question_id = str(question.get("question_id"))
            if question_id in open_answer_correctness:
                return open_answer_correctness[question_id]
            actual = answer.get("answer_text")
            expected = question.get("expected_answer")
            if not isinstance(actual, str) or not isinstance(expected, str):
                return False
            return self._normalize_text(actual) == self._normalize_text(expected)

        selected_option_id = answer.get("selected_option_id")
        if selected_option_id is None:
            return False
        correct_ids = {
            str(option["option_id"])
            for option in question.get("options", [])
            if option.get("option_id") is not None and option.get("is_correct") is True
        }
        return str(selected_option_id) in correct_ids

    def _normalize_text(self, value: str) -> str:
        normalized = unicodedata.normalize("NFKC", value).casefold()
        return " ".join(normalized.split())

    def _as_decimal(self, value: Any) -> Decimal:
        return Decimal(str(value))
