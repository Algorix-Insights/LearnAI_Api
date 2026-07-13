from __future__ import annotations

import asyncio
from copy import deepcopy
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api.dependencies import get_current_user, get_exam_attempt_workflow_use_case
from app.api.v1.resources.attempts import router as attempts_router
from app.api.v1.resources.exams import router as exams_router
from app.application.interfaces.open_answer_verifier import OpenAnswerVerification
from app.application.usecases.exam_attempts import ExamAttemptWorkflowUseCase
from app.core.exceptions import ApiError, BadRequestError, ResourceNotFoundError, UnauthorizedError
from app.domain.schemas.resources.attempts import SubmitAttemptAnswerRequest
from app.domain.schemas.resources.users import UserRead

USER_A = UUID("00000000-0000-0000-0000-000000000001")
USER_B = UUID("00000000-0000-0000-0000-000000000002")
NOTEBOOK_ID = UUID("00000000-0000-0000-0000-000000000010")
EXAM_ID = UUID("00000000-0000-0000-0000-000000000020")
ATTEMPT_ID = UUID("00000000-0000-0000-0000-000000000030")
QUESTION_CHOICE = UUID("00000000-0000-0000-0000-000000000040")
QUESTION_OPEN = UUID("00000000-0000-0000-0000-000000000041")
OPTION_WRONG = UUID("00000000-0000-0000-0000-000000000050")
OPTION_CORRECT = UUID("00000000-0000-0000-0000-000000000051")
FOREIGN_OPTION = UUID("00000000-0000-0000-0000-000000000052")


class FakeExamAttemptRepository:
    def __init__(self) -> None:
        self.exam = {
            "exam_id": str(EXAM_ID),
            "notebook_id": str(NOTEBOOK_ID),
            "status": "active",
        }
        self.allowed_users = {str(USER_A), str(USER_B)}
        self.questions = [
            {
                "question_id": str(QUESTION_CHOICE),
                "type": "multiple_choice",
                "statement": "Capital de Francia",
                "expected_answer": None,
                "question_order": 1,
                "points": "2.00",
                "options": [
                    {
                        "option_id": str(OPTION_WRONG),
                        "question_id": str(QUESTION_CHOICE),
                        "option_text": "Madrid",
                        "is_correct": False,
                        "option_order": 1,
                    },
                    {
                        "option_id": str(OPTION_CORRECT),
                        "question_id": str(QUESTION_CHOICE),
                        "option_text": "Paris",
                        "is_correct": True,
                        "option_order": 2,
                    },
                ],
            },
            {
                "question_id": str(QUESTION_OPEN),
                "type": "open",
                "statement": "Que convierte la fotosintesis?",
                "expected_answer": "Energia luminica en energia quimica",
                "question_order": 2,
                "points": "3.00",
                "options": [],
            },
        ]
        self.attempts: dict[str, dict[str, Any]] = {}
        self.answers: dict[tuple[str, str], dict[str, Any]] = {}
        self.last_grades: list[dict[str, Any]] = []

    async def get_exam(self, *, exam_id: str) -> dict[str, Any] | None:
        return deepcopy(self.exam) if exam_id == str(EXAM_ID) else None

    async def has_notebook_access(self, *, notebook_id: str, user_id: str) -> bool:
        return notebook_id == str(NOTEBOOK_ID) and user_id in self.allowed_users

    async def list_exam_questions(self, *, exam_id: str) -> list[dict[str, Any]]:
        return deepcopy(self.questions) if exam_id == str(EXAM_ID) else []

    async def get_active_attempt(
        self, *, exam_id: str, user_id: str
    ) -> dict[str, Any] | None:
        return next(
            (
                deepcopy(attempt)
                for attempt in self.attempts.values()
                if attempt["exam_id"] == exam_id
                and attempt["user_id"] == user_id
                and attempt["status"] == "in_progress"
            ),
            None,
        )

    async def create_workflow_attempt(
        self, *, exam_id: str, user_id: str, started_at: datetime
    ) -> dict[str, Any] | None:
        if await self.get_active_attempt(exam_id=exam_id, user_id=user_id):
            return None
        attempt_id = str(ATTEMPT_ID) if not self.attempts else str(UUID(int=31 + len(self.attempts)))
        attempt = {
            "attempt_id": attempt_id,
            "exam_id": exam_id,
            "user_id": user_id,
            "status": "in_progress",
            "score": 0,
            "started_at": started_at,
            "completed_at": None,
            "spent_time": 0,
        }
        self.attempts[attempt_id] = attempt
        return deepcopy(attempt)

    async def get_attempt_for_user(
        self, *, attempt_id: str, user_id: str
    ) -> dict[str, Any] | None:
        attempt = self.attempts.get(attempt_id)
        if attempt is None or attempt["user_id"] != user_id:
            return None
        return deepcopy(attempt)

    async def list_attempt_answers(self, *, attempt_id: str) -> list[dict[str, Any]]:
        return [
            deepcopy(answer)
            for (answer_attempt_id, _), answer in self.answers.items()
            if answer_attempt_id == attempt_id
        ]

    async def submit_workflow_answer(
        self,
        *,
        attempt_id: str,
        user_id: str,
        question_id: str,
        selected_option_id: str | None,
        answer_text: str | None,
    ) -> dict[str, Any] | None:
        attempt = self.attempts.get(attempt_id)
        if attempt is None or attempt["user_id"] != user_id or attempt["status"] != "in_progress":
            return None
        key = (attempt_id, question_id)
        existing = self.answers.get(key)
        answer = {
            "answer_id": existing["answer_id"] if existing else str(UUID(int=100 + len(self.answers))),
            "attempt_id": attempt_id,
            "question_id": question_id,
            "selected_option_id": selected_option_id,
            "answer_text": answer_text,
            "is_correct": None,
            "points_awarded": "0.00",
            "created_at": existing["created_at"] if existing else datetime.now(UTC),
        }
        self.answers[key] = answer
        return deepcopy(answer)

    async def finalize_workflow_attempt(
        self,
        *,
        attempt_id: str,
        user_id: str,
        completed_at: datetime,
        spent_time: int,
        grades: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        attempt = self.attempts.get(attempt_id)
        if attempt is None or attempt["user_id"] != user_id or attempt["status"] != "in_progress":
            return None
        self.last_grades = deepcopy(grades)
        grades_by_answer = {grade["answer_id"]: grade for grade in grades}
        for answer in self.answers.values():
            grade = grades_by_answer.get(answer["answer_id"])
            if answer["attempt_id"] == attempt_id and grade:
                answer["is_correct"] = grade["is_correct"]
                answer["points_awarded"] = grade["points_awarded"]

        earned = sum(
            Decimal(str(answer["points_awarded"]))
            for answer in self.answers.values()
            if answer["attempt_id"] == attempt_id
        )
        total = sum(Decimal(str(question["points"])) for question in self.questions)
        score = Decimal("0") if not total else (earned / total * 100).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        attempt.update(
            {
                "status": "completed",
                "score": str(score),
                "completed_at": completed_at,
                "spent_time": spent_time,
            }
        )
        return deepcopy(attempt)


class FakeOpenAnswerVerifier:
    def __init__(self, is_correct: bool) -> None:
        self.is_correct = is_correct
        self.calls: list[dict[str, str]] = []

    async def verify(
        self,
        *,
        question: str,
        expected_answer: str,
        submitted_answer: str,
    ) -> OpenAnswerVerification:
        self.calls.append(
            {
                "question": question,
                "expected_answer": expected_answer,
                "submitted_answer": submitted_answer,
            }
        )
        return OpenAnswerVerification(
            is_correct=self.is_correct,
            confidence=0.94,
            feedback="Equivalente semanticamente",
        )


class FailingOpenAnswerVerifier:
    def __init__(self) -> None:
        self.calls = 0

    async def verify(
        self,
        *,
        question: str,
        expected_answer: str,
        submitted_answer: str,
    ) -> OpenAnswerVerification:
        self.calls += 1
        raise RuntimeError("provider unavailable")


def test_start_is_safe_and_rejects_second_active_attempt() -> None:
    asyncio.run(_start_is_safe_and_rejects_second_active_attempt())


async def _start_is_safe_and_rejects_second_active_attempt() -> None:
    repository = FakeExamAttemptRepository()
    use_case = ExamAttemptWorkflowUseCase(repository)

    response = await use_case.start(exam_id=EXAM_ID, user_id=USER_A)
    body = response.model_dump(mode="json")

    assert body["data"]["attempt_id"] == str(ATTEMPT_ID)
    serialized = str(body)
    assert "expected_answer" not in serialized
    assert "is_correct" not in serialized
    assert "points_awarded" not in serialized
    assert "user_id" not in serialized
    assert [option["option_text"] for option in body["data"]["questions"][0]["options"]] == [
        "Madrid",
        "Paris",
    ]

    with pytest.raises(ApiError) as duplicate:
        await use_case.start(exam_id=EXAM_ID, user_id=USER_A)
    assert duplicate.value.status_code == 409


def test_start_hides_exam_existence_and_rejects_unavailable_exam() -> None:
    asyncio.run(_start_hides_exam_existence_and_rejects_unavailable_exam())


async def _start_hides_exam_existence_and_rejects_unavailable_exam() -> None:
    inaccessible = FakeExamAttemptRepository()
    inaccessible.allowed_users.remove(str(USER_A))
    with pytest.raises(ResourceNotFoundError):
        await ExamAttemptWorkflowUseCase(inaccessible).start(exam_id=EXAM_ID, user_id=USER_A)

    inactive = FakeExamAttemptRepository()
    inactive.exam["status"] = "archived"
    with pytest.raises(ResourceNotFoundError):
        await ExamAttemptWorkflowUseCase(inactive).start(exam_id=EXAM_ID, user_id=USER_A)

    empty = FakeExamAttemptRepository()
    empty.questions = []
    with pytest.raises(BadRequestError):
        await ExamAttemptWorkflowUseCase(empty).start(exam_id=EXAM_ID, user_id=USER_A)


def test_submit_upserts_without_accepting_or_returning_grading_fields() -> None:
    asyncio.run(_submit_upserts_without_accepting_or_returning_grading_fields())


async def _submit_upserts_without_accepting_or_returning_grading_fields() -> None:
    repository = FakeExamAttemptRepository()
    use_case = ExamAttemptWorkflowUseCase(repository)
    await use_case.start(exam_id=EXAM_ID, user_id=USER_A)

    response = await use_case.submit_answer(
        attempt_id=ATTEMPT_ID,
        question_id=QUESTION_CHOICE,
        user_id=USER_A,
        request=SubmitAttemptAnswerRequest(selected_option_id=OPTION_CORRECT),
    )
    first_answer_id = response.data.answer_id
    assert response.data.selected_option_id == OPTION_CORRECT
    assert "is_correct" not in response.model_dump(mode="json")["data"]
    assert "points_awarded" not in response.model_dump(mode="json")["data"]

    updated = await use_case.submit_answer(
        attempt_id=ATTEMPT_ID,
        question_id=QUESTION_CHOICE,
        user_id=USER_A,
        request=SubmitAttemptAnswerRequest(selected_option_id=OPTION_WRONG),
    )
    assert updated.data.answer_id == first_answer_id
    assert updated.data.selected_option_id == OPTION_WRONG

    with pytest.raises(BadRequestError):
        await use_case.submit_answer(
            attempt_id=ATTEMPT_ID,
            question_id=QUESTION_CHOICE,
            user_id=USER_A,
            request=SubmitAttemptAnswerRequest(selected_option_id=FOREIGN_OPTION),
        )

    with pytest.raises(ValidationError):
        SubmitAttemptAnswerRequest.model_validate(
            {"selected_option_id": str(OPTION_CORRECT), "is_correct": True}
        )


def test_submission_type_and_question_membership_are_enforced() -> None:
    asyncio.run(_submission_type_and_question_membership_are_enforced())


async def _submission_type_and_question_membership_are_enforced() -> None:
    repository = FakeExamAttemptRepository()
    use_case = ExamAttemptWorkflowUseCase(repository)
    await use_case.start(exam_id=EXAM_ID, user_id=USER_A)

    with pytest.raises(BadRequestError):
        await use_case.submit_answer(
            attempt_id=ATTEMPT_ID,
            question_id=QUESTION_OPEN,
            user_id=USER_A,
            request=SubmitAttemptAnswerRequest(selected_option_id=OPTION_CORRECT),
        )
    with pytest.raises(BadRequestError):
        await use_case.submit_answer(
            attempt_id=ATTEMPT_ID,
            question_id=QUESTION_CHOICE,
            user_id=USER_A,
            request=SubmitAttemptAnswerRequest(answer_text="Paris"),
        )
    with pytest.raises(BadRequestError):
        await use_case.submit_answer(
            attempt_id=ATTEMPT_ID,
            question_id=QUESTION_OPEN,
            user_id=USER_A,
            request=SubmitAttemptAnswerRequest(answer_text="   "),
        )
    with pytest.raises(ResourceNotFoundError):
        await use_case.submit_answer(
            attempt_id=ATTEMPT_ID,
            question_id=UUID(int=999),
            user_id=USER_A,
            request=SubmitAttemptAnswerRequest(answer_text="No pertenece"),
        )


def test_session_returns_only_student_safe_answer_state() -> None:
    asyncio.run(_session_returns_only_student_safe_answer_state())


async def _session_returns_only_student_safe_answer_state() -> None:
    repository = FakeExamAttemptRepository()
    use_case = ExamAttemptWorkflowUseCase(repository)
    await use_case.start(exam_id=EXAM_ID, user_id=USER_A)
    await use_case.submit_answer(
        attempt_id=ATTEMPT_ID,
        question_id=QUESTION_CHOICE,
        user_id=USER_A,
        request=SubmitAttemptAnswerRequest(selected_option_id=OPTION_CORRECT),
    )

    session = await use_case.get_session(attempt_id=ATTEMPT_ID, user_id=USER_A)
    body = session.model_dump(mode="json")

    assert body["data"]["answers"][0]["selected_option_id"] == str(OPTION_CORRECT)
    serialized = str(body)
    assert "expected_answer" not in serialized
    assert "is_correct" not in serialized
    assert "points_awarded" not in serialized


def test_attempt_ownership_is_scoped_to_authenticated_user() -> None:
    asyncio.run(_attempt_ownership_is_scoped_to_authenticated_user())


async def _attempt_ownership_is_scoped_to_authenticated_user() -> None:
    repository = FakeExamAttemptRepository()
    use_case = ExamAttemptWorkflowUseCase(repository)
    await use_case.start(exam_id=EXAM_ID, user_id=USER_A)

    with pytest.raises(ResourceNotFoundError):
        await use_case.get_session(attempt_id=ATTEMPT_ID, user_id=USER_B)
    with pytest.raises(ResourceNotFoundError):
        await use_case.submit_answer(
            attempt_id=ATTEMPT_ID,
            question_id=QUESTION_CHOICE,
            user_id=USER_B,
            request=SubmitAttemptAnswerRequest(selected_option_id=OPTION_CORRECT),
        )
    with pytest.raises(ResourceNotFoundError):
        await use_case.finish(attempt_id=ATTEMPT_ID, user_id=USER_B)


def test_finish_calculates_weighted_score_server_side_and_closes_attempt() -> None:
    asyncio.run(_finish_calculates_weighted_score_server_side_and_closes_attempt())


async def _finish_calculates_weighted_score_server_side_and_closes_attempt() -> None:
    repository = FakeExamAttemptRepository()
    use_case = ExamAttemptWorkflowUseCase(repository)
    await use_case.start(exam_id=EXAM_ID, user_id=USER_A)
    await use_case.submit_answer(
        attempt_id=ATTEMPT_ID,
        question_id=QUESTION_CHOICE,
        user_id=USER_A,
        request=SubmitAttemptAnswerRequest(selected_option_id=OPTION_CORRECT),
    )
    await use_case.submit_answer(
        attempt_id=ATTEMPT_ID,
        question_id=QUESTION_OPEN,
        user_id=USER_A,
        request=SubmitAttemptAnswerRequest(answer_text="  ENERGIA luminica en energia QUIMICA "),
    )

    finished = await use_case.finish(attempt_id=ATTEMPT_ID, user_id=USER_A)

    assert finished.data.score == 100.0
    assert finished.data.earned_points == 5.0
    assert finished.data.total_points == 5.0
    assert finished.data.answered_questions == 2
    assert all("answer_id" in grade for grade in repository.last_grades)
    assert repository.attempts[str(ATTEMPT_ID)]["status"] == "completed"

    with pytest.raises(ApiError) as second_finish:
        await use_case.finish(attempt_id=ATTEMPT_ID, user_id=USER_A)
    assert second_finish.value.status_code == 409
    with pytest.raises(ApiError) as late_answer:
        await use_case.submit_answer(
            attempt_id=ATTEMPT_ID,
            question_id=QUESTION_CHOICE,
            user_id=USER_A,
            request=SubmitAttemptAnswerRequest(selected_option_id=OPTION_WRONG),
        )
    assert late_answer.value.status_code == 409


def test_finish_counts_unanswered_questions_as_zero_weighted_points() -> None:
    asyncio.run(_finish_counts_unanswered_questions_as_zero_weighted_points())


async def _finish_counts_unanswered_questions_as_zero_weighted_points() -> None:
    repository = FakeExamAttemptRepository()
    use_case = ExamAttemptWorkflowUseCase(repository)
    await use_case.start(exam_id=EXAM_ID, user_id=USER_A)
    await use_case.submit_answer(
        attempt_id=ATTEMPT_ID,
        question_id=QUESTION_CHOICE,
        user_id=USER_A,
        request=SubmitAttemptAnswerRequest(selected_option_id=OPTION_CORRECT),
    )

    finished = await use_case.finish(attempt_id=ATTEMPT_ID, user_id=USER_A)

    assert finished.data.score == 40.0
    assert finished.data.earned_points == 2.0
    assert finished.data.total_points == 5.0
    assert finished.data.answered_questions == 1
    assert finished.data.total_questions == 2


def test_async_open_answer_verifier_can_override_exact_match_fallback() -> None:
    asyncio.run(_async_open_answer_verifier_can_override_exact_match_fallback())


async def _async_open_answer_verifier_can_override_exact_match_fallback() -> None:
    repository = FakeExamAttemptRepository()
    verifier = FakeOpenAnswerVerifier(is_correct=True)
    use_case = ExamAttemptWorkflowUseCase(repository, open_answer_verifier=verifier)
    await use_case.start(exam_id=EXAM_ID, user_id=USER_A)
    await use_case.submit_answer(
        attempt_id=ATTEMPT_ID,
        question_id=QUESTION_OPEN,
        user_id=USER_A,
        request=SubmitAttemptAnswerRequest(
            answer_text="Las plantas guardan la luz como energia util para sus celulas."
        ),
    )

    finished = await use_case.finish(attempt_id=ATTEMPT_ID, user_id=USER_A)

    assert finished.data.score == 60.0
    assert len(verifier.calls) == 1
    assert verifier.calls[0]["question"] == "Que convierte la fotosintesis?"


def test_verifier_failure_uses_deterministic_normalized_fallback() -> None:
    asyncio.run(_verifier_failure_uses_deterministic_normalized_fallback())


async def _verifier_failure_uses_deterministic_normalized_fallback() -> None:
    repository = FakeExamAttemptRepository()
    verifier = FailingOpenAnswerVerifier()
    use_case = ExamAttemptWorkflowUseCase(repository, open_answer_verifier=verifier)
    await use_case.start(exam_id=EXAM_ID, user_id=USER_A)
    await use_case.submit_answer(
        attempt_id=ATTEMPT_ID,
        question_id=QUESTION_OPEN,
        user_id=USER_A,
        request=SubmitAttemptAnswerRequest(
            answer_text="  ENERGIA luminica EN energia quimica  "
        ),
    )

    finished = await use_case.finish(attempt_id=ATTEMPT_ID, user_id=USER_A)

    assert verifier.calls == 1
    assert finished.data.score == 60.0


def test_http_workflow_requires_auth_and_rejects_grade_tampering() -> None:
    repository = FakeExamAttemptRepository()
    use_case = ExamAttemptWorkflowUseCase(repository)
    app = _test_app(use_case=use_case, current_user=UserRead(user_id=USER_A))

    with TestClient(app) as client:
        start = client.post(f"/api/v1/exams/{EXAM_ID}/attempts", json={})
        assert start.status_code == 201
        assert "is_correct" not in str(start.json())

        tampered_start = client.post(
            f"/api/v1/exams/{EXAM_ID}/attempts",
            json={"user_id": str(USER_B), "status": "completed", "score": 100},
        )
        assert tampered_start.status_code == 422

        tampered_answer = client.put(
            f"/api/v1/attempts/{ATTEMPT_ID}/answers/{QUESTION_CHOICE}",
            json={
                "selected_option_id": str(OPTION_CORRECT),
                "is_correct": True,
                "points_awarded": 999,
            },
        )
        assert tampered_answer.status_code == 422

        tampered_finish = client.post(
            f"/api/v1/attempts/{ATTEMPT_ID}/finish",
            json={"score": 100},
        )
        assert tampered_finish.status_code == 422

    unauthorized_app = _test_app(use_case=ExamAttemptWorkflowUseCase(FakeExamAttemptRepository()))
    with TestClient(unauthorized_app, raise_server_exceptions=False) as client:
        unauthorized = client.post(f"/api/v1/exams/{EXAM_ID}/attempts", json={})
    assert unauthorized.status_code == 401


def _test_app(
    *,
    use_case: ExamAttemptWorkflowUseCase,
    current_user: UserRead | None = None,
) -> FastAPI:
    app = FastAPI()

    async def api_error_handler(_: object, exc: ApiError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    async def authenticated_user() -> UserRead:
        if current_user is None:
            raise UnauthorizedError()
        return current_user

    app.add_exception_handler(ApiError, api_error_handler)
    app.include_router(exams_router, prefix="/api/v1")
    app.include_router(attempts_router, prefix="/api/v1")
    app.dependency_overrides[get_current_user] = authenticated_user
    app.dependency_overrides[get_exam_attempt_workflow_use_case] = lambda: use_case
    return app
