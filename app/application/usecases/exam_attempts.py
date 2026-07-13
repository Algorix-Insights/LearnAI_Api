from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from app.application.interfaces.open_answer_verifier import (
    OpenAnswerVerification,
    OpenAnswerVerifier,
)
from app.core.exceptions import ApiError, BadRequestError, ForbiddenError, ResourceNotFoundError
from app.domain.interfaces.attempts import ExamAttemptWorkflowRepository
from app.domain.schemas.resources.attempts import (
    AttemptQuestionOptionRead,
    AttemptQuestionRead,
    AttemptSessionRead,
    AttemptSessionResponse,
    FinishedAttemptRead,
    FinishedAttemptResponse,
    GradedAttemptAnswerRead,
    SubmitAttemptAnswerRequest,
    SubmittedAttemptAnswerRead,
    SubmittedAttemptAnswerResponse,
)
from app.domain.services.exam_attempts import ExamAttemptGrader
from app.infra.repositories.ai_usage import AiUsageRepository


class ExamAttemptWorkflowUseCase:
    def __init__(
        self,
        repository: ExamAttemptWorkflowRepository,
        grader: ExamAttemptGrader | None = None,
        open_answer_verifier: OpenAnswerVerifier | None = None,
        usage: AiUsageRepository | None = None,
    ) -> None:
        self.repository = repository
        self.grader = grader or ExamAttemptGrader()
        self.open_answer_verifier = open_answer_verifier
        self.usage = usage

    async def start(self, *, exam_id: UUID, user_id: UUID) -> AttemptSessionResponse:
        await self._require_exam(exam_id=exam_id, user_id=user_id)
        questions = await self.repository.list_exam_questions(exam_id=str(exam_id))
        if not questions:
            raise BadRequestError("El examen no tiene preguntas disponibles.")

        active = await self.repository.get_active_attempt(
            exam_id=str(exam_id), user_id=str(user_id)
        )
        if active is not None:
            answers = await self.repository.list_attempt_answers(
                attempt_id=str(active["attempt_id"])
            )
            return self._session_response(
                attempt=active,
                questions=questions,
                answers=answers,
            )

        attempt = await self.repository.create_workflow_attempt(
            exam_id=str(exam_id),
            user_id=str(user_id),
            started_at=datetime.now(UTC),
        )
        if attempt is None:
            # A concurrent start may have won the unique-index race. Returning
            # that session makes POST start a safe recovery operation.
            attempt = await self.repository.get_active_attempt(
                exam_id=str(exam_id), user_id=str(user_id)
            )
            if attempt is None:
                raise self._conflict("No fue posible iniciar el intento.")
        return self._session_response(attempt=attempt, questions=questions, answers=[])

    async def get_session(
        self, *, attempt_id: UUID, user_id: UUID
    ) -> AttemptSessionResponse:
        attempt = await self._require_owned_attempt(attempt_id=attempt_id, user_id=user_id)
        await self._require_attempt_access(attempt=attempt, user_id=user_id)
        questions = await self.repository.list_exam_questions(exam_id=str(attempt["exam_id"]))
        answers = await self.repository.list_attempt_answers(attempt_id=str(attempt_id))
        return self._session_response(
            attempt=attempt,
            questions=questions,
            answers=answers,
        )

    async def submit_answer(
        self,
        *,
        attempt_id: UUID,
        question_id: UUID,
        user_id: UUID,
        request: SubmitAttemptAnswerRequest,
    ) -> SubmittedAttemptAnswerResponse:
        attempt = await self._require_owned_attempt(attempt_id=attempt_id, user_id=user_id)
        await self._require_attempt_access(attempt=attempt, user_id=user_id)
        self._require_in_progress(attempt)

        questions = await self.repository.list_exam_questions(exam_id=str(attempt["exam_id"]))
        question = next(
            (item for item in questions if str(item.get("question_id")) == str(question_id)),
            None,
        )
        if question is None:
            raise ResourceNotFoundError()

        selected_option_id, answer_text = self._validate_submission(
            question=question,
            request=request,
        )
        answer = await self.repository.submit_workflow_answer(
            attempt_id=str(attempt_id),
            user_id=str(user_id),
            question_id=str(question_id),
            selected_option_id=selected_option_id,
            answer_text=answer_text,
        )
        if answer is None:
            raise self._conflict("El intento ya no acepta respuestas.")
        return SubmittedAttemptAnswerResponse(data=self._safe_answer(answer))

    async def finish(
        self, *, attempt_id: UUID, user_id: UUID
    ) -> FinishedAttemptResponse:
        attempt = await self._require_owned_attempt(attempt_id=attempt_id, user_id=user_id)
        await self._require_attempt_access(attempt=attempt, user_id=user_id)
        self._require_in_progress(attempt)

        questions = await self.repository.list_exam_questions(exam_id=str(attempt["exam_id"]))
        if not questions:
            raise BadRequestError("El examen no tiene preguntas disponibles.")
        answers = await self.repository.list_attempt_answers(attempt_id=str(attempt_id))
        open_answer_count = self._answered_open_question_count(
            questions=questions,
            answers=answers,
        )
        if self.open_answer_verifier is not None and self.usage is not None and open_answer_count:
            await self.usage.reserve(
                actor_id=str(user_id),
                operation="exam_grading",
                units=open_answer_count,
            )
        open_verifications = await self._verify_open_answers(
            questions=questions,
            answers=answers,
        )
        grade = self.grader.grade(
            questions=questions,
            answers=answers,
            open_answer_correctness={
                question_id: verification.is_correct
                for question_id, verification in open_verifications.items()
            },
        )

        completed_at = datetime.now(UTC)
        started_at = self._as_datetime(attempt.get("started_at"))
        spent_time = max(0, int((completed_at - started_at).total_seconds()))
        finished = await self.repository.finalize_workflow_attempt(
            attempt_id=str(attempt_id),
            user_id=str(user_id),
            completed_at=completed_at,
            spent_time=spent_time,
            grades=grade.grades,
        )
        if finished is None:
            raise self._conflict("El intento ya fue finalizado.")

        return FinishedAttemptResponse(
            data=FinishedAttemptRead(
                attempt_id=UUID(str(finished["attempt_id"])),
                exam_id=UUID(str(finished["exam_id"])),
                status=str(finished["status"]),
                attempt_number=int(finished.get("attempt_number") or 1),
                attempts_remaining=max(
                    0,
                    5 - int(finished.get("attempt_number") or 1),
                ),
                score=float(finished["score"]),
                earned_points=float(grade.earned_points),
                total_points=float(grade.total_points),
                answered_questions=grade.answered_questions,
                total_questions=grade.total_questions,
                completed_at=self._as_datetime(finished.get("completed_at") or completed_at),
                spent_time=int(finished.get("spent_time", spent_time)),
                answers=self._graded_answers(
                    grades=grade.grades,
                    verifications=open_verifications,
                ),
            )
        )

    async def _require_exam(self, *, exam_id: UUID, user_id: UUID) -> dict[str, Any]:
        exam = await self.repository.get_exam(exam_id=str(exam_id))
        if exam is None or exam.get("status") != "active":
            raise ResourceNotFoundError()
        allowed = await self.repository.has_notebook_access(
            notebook_id=str(exam["notebook_id"]),
            user_id=str(user_id),
        )
        if not allowed:
            # Match the missing/inactive response so exam UUIDs cannot be enumerated.
            raise ResourceNotFoundError()
        return exam

    async def _require_owned_attempt(
        self, *, attempt_id: UUID, user_id: UUID
    ) -> dict[str, Any]:
        attempt = await self.repository.get_attempt_for_user(
            attempt_id=str(attempt_id), user_id=str(user_id)
        )
        if attempt is None:
            # Same response for missing and foreign attempts prevents an ownership oracle.
            raise ResourceNotFoundError()
        return attempt

    async def _require_attempt_access(
        self, *, attempt: dict[str, Any], user_id: UUID
    ) -> None:
        exam = await self.repository.get_exam(exam_id=str(attempt["exam_id"]))
        if exam is None:
            raise ResourceNotFoundError()
        allowed = await self.repository.has_notebook_access(
            notebook_id=str(exam["notebook_id"]),
            user_id=str(user_id),
        )
        if not allowed:
            raise ForbiddenError()

    def _require_in_progress(self, attempt: dict[str, Any]) -> None:
        if attempt.get("status") != "in_progress":
            raise self._conflict("El intento ya no acepta respuestas.")

    def _validate_submission(
        self,
        *,
        question: dict[str, Any],
        request: SubmitAttemptAnswerRequest,
    ) -> tuple[str | None, str | None]:
        if question.get("type") == "open":
            if request.answer_text is None:
                raise BadRequestError("La pregunta abierta requiere una respuesta de texto.")
            answer_text = request.answer_text.strip()
            if not answer_text:
                raise BadRequestError("La respuesta de texto no puede estar vacia.")
            return None, answer_text

        if request.selected_option_id is None:
            raise BadRequestError("Debe seleccionar una opcion para esta pregunta.")
        valid_option_ids = {
            str(option["option_id"])
            for option in question.get("options", [])
            if option.get("option_id") is not None
        }
        if str(request.selected_option_id) not in valid_option_ids:
            raise BadRequestError("La opcion no pertenece a la pregunta.")
        return str(request.selected_option_id), None

    def _session_response(
        self,
        *,
        attempt: dict[str, Any],
        questions: list[dict[str, Any]],
        answers: list[dict[str, Any]],
    ) -> AttemptSessionResponse:
        safe_questions = [
            AttemptQuestionRead(
                question_id=UUID(str(question["question_id"])),
                type=str(question["type"]),
                statement=str(question["statement"]),
                question_order=int(question["question_order"]),
                points=float(question["points"]),
                options=[
                    AttemptQuestionOptionRead(
                        option_id=UUID(str(option["option_id"])),
                        option_text=str(option["option_text"]),
                        option_order=int(option["option_order"]),
                    )
                    for option in question.get("options", [])
                ],
            )
            for question in questions
        ]
        return AttemptSessionResponse(
            data=AttemptSessionRead(
                attempt_id=UUID(str(attempt["attempt_id"])),
                exam_id=UUID(str(attempt["exam_id"])),
                status=str(attempt["status"]),
                attempt_number=int(attempt.get("attempt_number") or 1),
                attempts_remaining=max(
                    0,
                    5 - int(attempt.get("attempt_number") or 1),
                ),
                started_at=self._optional_datetime(attempt.get("started_at")),
                questions=safe_questions,
                answers=[self._safe_answer(answer) for answer in answers],
            )
        )

    async def _verify_open_answers(
        self,
        *,
        questions: list[dict[str, Any]],
        answers: list[dict[str, Any]],
    ) -> dict[str, OpenAnswerVerification]:
        if self.open_answer_verifier is None:
            return {}

        answers_by_question = {
            str(answer["question_id"]): answer
            for answer in answers
            if answer.get("question_id") is not None
        }
        results: dict[str, OpenAnswerVerification] = {}
        for question in questions:
            if question.get("type") != "open":
                continue
            question_id = str(question.get("question_id"))
            answer = answers_by_question.get(question_id)
            expected_answer = question.get("expected_answer")
            submitted_answer = answer.get("answer_text") if answer else None
            if not isinstance(expected_answer, str) or not isinstance(submitted_answer, str):
                continue
            try:
                verification = await self.open_answer_verifier.verify(
                    question=str(question.get("statement", "")),
                    expected_answer=expected_answer,
                    submitted_answer=submitted_answer,
                )
            except Exception:
                # Deterministic normalized equality remains the safe fallback.
                continue
            results[question_id] = verification
        return results

    def _answered_open_question_count(
        self,
        *,
        questions: list[dict[str, Any]],
        answers: list[dict[str, Any]],
    ) -> int:
        answered = {
            str(answer.get("question_id"))
            for answer in answers
            if isinstance(answer.get("answer_text"), str)
        }
        return sum(
            1
            for question in questions
            if question.get("type") == "open"
            and str(question.get("question_id")) in answered
        )

    def _graded_answers(
        self,
        *,
        grades: list[dict[str, Any]],
        verifications: dict[str, OpenAnswerVerification],
    ) -> list[GradedAttemptAnswerRead]:
        result: list[GradedAttemptAnswerRead] = []
        for grade in grades:
            question_id = str(grade["question_id"])
            verification = verifications.get(question_id)
            result.append(
                GradedAttemptAnswerRead(
                    answer_id=UUID(str(grade["answer_id"])),
                    question_id=UUID(question_id),
                    is_correct=bool(grade["is_correct"]),
                    points_awarded=float(grade["points_awarded"]),
                    confidence=verification.confidence if verification else None,
                    feedback=verification.feedback if verification else None,
                )
            )
        return result

    def _safe_answer(self, answer: dict[str, Any]) -> SubmittedAttemptAnswerRead:
        return SubmittedAttemptAnswerRead(
            answer_id=UUID(str(answer["answer_id"])),
            attempt_id=UUID(str(answer["attempt_id"])),
            question_id=UUID(str(answer["question_id"])),
            selected_option_id=(
                UUID(str(answer["selected_option_id"]))
                if answer.get("selected_option_id") is not None
                else None
            ),
            answer_text=answer.get("answer_text"),
            created_at=self._optional_datetime(answer.get("created_at")),
        )

    def _as_datetime(self, value: Any) -> datetime:
        parsed = self._optional_datetime(value)
        return parsed or datetime.now(UTC)

    def _optional_datetime(self, value: Any) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            parsed = value
        else:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)

    def _conflict(self, message: str) -> ApiError:
        return ApiError(409, message)
