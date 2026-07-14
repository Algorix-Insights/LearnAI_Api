from __future__ import annotations

from collections import Counter
from typing import Any, Mapping
from uuid import UUID

from app.application.usecases.rag_support.common import RagAccessPolicy
from app.application.usecases.rag_support.llm import RagLlmService
from app.core.exceptions import BadRequestError, RepositoryError
from app.domain.schemas.entities import (
    ExamCreate,
    FlashcardCreate,
    QuestionCreate,
    QuestionOptionCreate,
)
from app.domain.schemas.resources.exams import (
    ExamQuestionRepositoryCreateRequest,
    ExamRepositoryCreateRequest,
)
from app.domain.schemas.resources.flashcards import FlashcardRepositoryCreateRequest
from app.domain.schemas.resources.question_options import QuestionOptionRepositoryCreateRequest
from app.domain.schemas.resources.questions import QuestionRepositoryCreateRequest
from app.domain.schemas.resources.rag import (
    ExamDraft,
    ExamGenerationRequest,
    ExamGenerationResponse,
    FlashcardDraftSet,
    FlashcardGenerationRequest,
    FlashcardGenerationResponse,
    FlashcardStudyListResponse,
    MultipleChoiceQuestionDraft,
    OpenQuestionDraft,
    TrueFalseQuestionDraft,
)
from app.infra.repositories.exams import ExamQuestionRepository, ExamRepository
from app.infra.repositories.flashcards import FlashcardRepository
from app.infra.repositories.question_options import QuestionOptionRepository
from app.infra.repositories.questions import QuestionRepository
from app.infra.repositories.rag_generation import RagGenerationRepository


QuestionDraft = MultipleChoiceQuestionDraft | TrueFalseQuestionDraft | OpenQuestionDraft

EXAM_BASE_OUTPUT_TOKENS = 500
EXAM_TRUE_FALSE_OUTPUT_TOKENS = 80
EXAM_MULTIPLE_CHOICE_OUTPUT_TOKENS = 200
EXAM_OPEN_OUTPUT_TOKENS = 250
MAX_EXAM_OUTPUT_TOKENS = 4_096


class RagStudyMaterialWorkflow:
    """Generates and persists flashcards and exams from retrieved notebook sources."""

    def __init__(
        self,
        *,
        exams: ExamRepository,
        exam_questions: ExamQuestionRepository,
        questions: QuestionRepository,
        question_options: QuestionOptionRepository,
        flashcards: FlashcardRepository,
        generation: RagGenerationRepository | None,
        llm: RagLlmService,
        policy: RagAccessPolicy,
    ) -> None:
        self.exams = exams
        self.exam_questions = exam_questions
        self.questions = questions
        self.question_options = question_options
        self.flashcards = flashcards
        self.generation = generation
        self.llm = llm
        self.policy = policy

    async def generate_flashcards(
        self,
        *,
        notebook_id: UUID,
        user_id: UUID,
        request: FlashcardGenerationRequest,
    ) -> FlashcardGenerationResponse:
        await self.policy.require_manage_access(user_id=user_id, notebook_id=notebook_id)
        model = self.llm.resolve_model(request.model)
        await self.policy.reserve_ai_usage(user_id, "flashcards")
        sources = await self.llm.generation_sources(
            notebook_id=notebook_id,
            purpose="conceptos, definiciones y hechos principales para crear flashcards",
        )
        draft = await self.llm.structured_completion(
            schema=FlashcardDraftSet,
            schema_name="notebook_flashcards",
            model=model,
            max_tokens=10000,
            instruction=(
                f"Genera exactamente {request.count} flashcards distintas. "
                "Cada pregunta debe poder responderse solo con el contexto y cada respuesta "
                "debe ser breve, precisa y autosuficiente."
            ),
            sources=sources,
        )
        if len(draft.flashcards) != request.count:
            raise BadRequestError("El modelo no genero la cantidad solicitada de flashcards.")

        if self.generation is not None:
            generated = await self.generation.persist_flashcards(
                actor_id=str(user_id),
                notebook_id=str(notebook_id),
                items=[
                    {
                        "question": item.question.strip(),
                        "answer": item.answer.strip(),
                    }
                    for item in draft.flashcards
                ],
            )
            return FlashcardGenerationResponse(data=generated, sources=sources)

        generated: list[dict[str, Any]] = []
        for item in draft.flashcards:
            question = await self.questions.create(
                QuestionRepositoryCreateRequest(
                    payload=QuestionCreate(
                        type="open",
                        statement=item.question.strip(),
                        expected_answer=item.answer.strip(),
                    )
                )
            )
            question_id = self._required_uuid(question, "question_id")
            flashcard = await self.flashcards.create(
                FlashcardRepositoryCreateRequest(
                    payload=FlashcardCreate(
                        notebook_id=notebook_id,
                        question_id=question_id,
                    )
                )
            )
            generated.append(
                {
                    "flashcard_id": self._required_uuid(flashcard, "flashcard_id"),
                    "question_id": question_id,
                    "question": item.question.strip(),
                    "answer": item.answer.strip(),
                }
            )
        return FlashcardGenerationResponse(data=generated, sources=sources)

    async def list_flashcards(
        self,
        *,
        notebook_id: UUID,
        user_id: UUID,
        limit: int,
        offset: int,
    ) -> FlashcardStudyListResponse:
        await self.policy.require_access(user_id=user_id, notebook_id=notebook_id)
        if self.generation is None:
            raise RepositoryError("listar las flashcards")
        data = await self.generation.list_flashcards(
            actor_id=str(user_id),
            notebook_id=str(notebook_id),
            limit=limit,
            offset=offset,
        )
        return FlashcardStudyListResponse(data=data, limit=limit, offset=offset)

    async def generate_exam(
        self,
        *,
        notebook_id: UUID,
        user_id: UUID,
        request: ExamGenerationRequest,
    ) -> ExamGenerationResponse:
        await self.policy.require_manage_access(user_id=user_id, notebook_id=notebook_id)
        model = self.llm.resolve_model(request.model)
        await self.policy.reserve_ai_usage(user_id, "exam")
        sources = await self.llm.generation_sources(
            notebook_id=notebook_id,
            purpose="conceptos, relaciones y detalles evaluables para crear un examen",
        )
        draft = await self.llm.structured_completion(
            schema=ExamDraft,
            schema_name="notebook_exam",
            model=model,
            max_tokens=self._exam_max_tokens(request),
            instruction=(
                f"Genera un examen con exactamente {request.true_false_count} preguntas "
                f"true_false, {request.multiple_choice_count} multiple_choice y "
                f"{request.open_count} open. Usa indices de opcion basados en cero. "
                "Las opciones incorrectas deben ser plausibles, pero inequívocamente falsas "
                "segun el contexto. Limites: titulo de 12 palabras, descripcion de 30, "
                "enunciados de 18, opciones de 8 y respuestas abiertas de 35. "
                "Cada multiple_choice debe tener exactamente 4 opciones."
            ),
            sources=sources,
        )
        self._validate_exam_counts(draft=draft, request=request)

        exam_name = request.name or draft.title.strip()
        exam_description = (
            request.description if request.description is not None else draft.description
        )
        if self.generation is not None:
            generated_exam = await self.generation.persist_exam(
                actor_id=str(user_id),
                notebook_id=str(notebook_id),
                name=exam_name,
                description=exam_description,
                questions=[self._question_persistence_payload(item) for item in draft.questions],
            )
            return ExamGenerationResponse(data=generated_exam, sources=sources)

        exam = await self.exams.create(
            ExamRepositoryCreateRequest(
                payload=ExamCreate(
                    notebook_id=notebook_id,
                    name=exam_name,
                    description=exam_description,
                )
            )
        )
        exam_id = self._required_uuid(exam, "exam_id")

        generated_questions: list[dict[str, Any]] = []
        for question_order, item in enumerate(draft.questions, start=1):
            expected_answer = (
                item.expected_answer.strip() if isinstance(item, OpenQuestionDraft) else None
            )
            question = await self.questions.create(
                QuestionRepositoryCreateRequest(
                    payload=QuestionCreate(
                        type=item.type,
                        statement=item.statement.strip(),
                        expected_answer=expected_answer,
                    )
                )
            )
            question_id = self._required_uuid(question, "question_id")
            await self.exam_questions.create(
                ExamQuestionRepositoryCreateRequest(
                    exam_id=exam_id,
                    question_id=question_id,
                    question_order=question_order,
                )
            )
            options = await self._persist_question_options(question_id=question_id, draft=item)
            generated_questions.append(
                {
                    "question_id": question_id,
                    "type": item.type,
                    "statement": item.statement.strip(),
                    "question_order": question_order,
                    "options": [
                        {
                            "option_id": option["option_id"],
                            "option_text": option["option_text"],
                            "option_order": option["option_order"],
                        }
                        for option in options
                    ],
                }
            )

        return ExamGenerationResponse(
            data={
                "exam_id": exam_id,
                "notebook_id": notebook_id,
                "name": exam_name,
                "description": exam_description,
                "status": exam.get("status") or "active",
                "questions": generated_questions,
            },
            sources=sources,
        )

    async def _persist_question_options(
        self,
        *,
        question_id: UUID,
        draft: QuestionDraft,
    ) -> list[dict[str, Any]]:
        option_values: list[tuple[str, bool]]
        if isinstance(draft, MultipleChoiceQuestionDraft):
            option_values = [
                (option, index == draft.correct_option_index)
                for index, option in enumerate(draft.options)
            ]
        elif isinstance(draft, TrueFalseQuestionDraft):
            option_values = [
                ("Verdadero", draft.correct_answer),
                ("Falso", not draft.correct_answer),
            ]
        else:
            return []

        persisted: list[dict[str, Any]] = []
        for option_order, (option_text, is_correct) in enumerate(option_values, start=1):
            option = await self.question_options.create(
                QuestionOptionRepositoryCreateRequest(
                    payload=QuestionOptionCreate(
                        question_id=question_id,
                        option_text=option_text,
                        is_correct=is_correct,
                        option_order=option_order,
                    )
                )
            )
            persisted.append(
                {
                    "option_id": self._required_uuid(option, "option_id"),
                    "option_text": option_text,
                    "is_correct": is_correct,
                    "option_order": option_order,
                }
            )
        return persisted

    @staticmethod
    def _question_persistence_payload(draft: QuestionDraft) -> dict[str, Any]:
        if isinstance(draft, MultipleChoiceQuestionDraft):
            options = [
                {
                    "option_text": option,
                    "is_correct": index == draft.correct_option_index,
                    "option_order": index + 1,
                }
                for index, option in enumerate(draft.options)
            ]
            expected_answer = None
        elif isinstance(draft, TrueFalseQuestionDraft):
            options = [
                {
                    "option_text": "Verdadero",
                    "is_correct": draft.correct_answer,
                    "option_order": 1,
                },
                {
                    "option_text": "Falso",
                    "is_correct": not draft.correct_answer,
                    "option_order": 2,
                },
            ]
            expected_answer = None
        else:
            options = []
            expected_answer = draft.expected_answer.strip()
        return {
            "type": draft.type,
            "statement": draft.statement.strip(),
            "expected_answer": expected_answer,
            "options": options,
        }

    @staticmethod
    def _validate_exam_counts(*, draft: ExamDraft, request: ExamGenerationRequest) -> None:
        actual = Counter(item.type for item in draft.questions)
        expected = {
            "true_false": request.true_false_count,
            "multiple_choice": request.multiple_choice_count,
            "open": request.open_count,
        }
        if any(actual[question_type] != count for question_type, count in expected.items()):
            raise BadRequestError("El modelo no genero la mezcla de preguntas solicitada.")

    @staticmethod
    def _exam_max_tokens(request: ExamGenerationRequest) -> int:
        estimated = (
            EXAM_BASE_OUTPUT_TOKENS
            + request.true_false_count * EXAM_TRUE_FALSE_OUTPUT_TOKENS
            + request.multiple_choice_count * EXAM_MULTIPLE_CHOICE_OUTPUT_TOKENS
            + request.open_count * EXAM_OPEN_OUTPUT_TOKENS
        )
        return min(MAX_EXAM_OUTPUT_TOKENS, estimated)

    @staticmethod
    def _required_uuid(data: Mapping[str, Any], field: str) -> UUID:
        try:
            return UUID(str(data[field]))
        except (KeyError, TypeError, ValueError) as exc:
            raise RepositoryError("persistir") from exc
