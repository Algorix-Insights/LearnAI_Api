from __future__ import annotations

import asyncio
from copy import deepcopy
from types import SimpleNamespace

import pytest

from app.core.exceptions import RepositoryError
from app.infra.repositories.rag_generation import RagGenerationRepository


ACTOR_ID = "00000000-0000-0000-0000-000000000001"
NOTEBOOK_ID = "00000000-0000-0000-0000-000000000002"
EXAM_ID = "00000000-0000-0000-0000-000000000003"
QUESTION_ID = "00000000-0000-0000-0000-000000000004"
OPTION_IDS = (
    "00000000-0000-0000-0000-000000000005",
    "00000000-0000-0000-0000-000000000006",
)


class FakeRpcQuery:
    def __init__(self, data) -> None:
        self.data = data

    def execute(self):
        return SimpleNamespace(data=self.data)


class FakeClient:
    def __init__(self, data) -> None:
        self.data = data
        self.calls: list[tuple[str, dict]] = []

    def rpc(self, function_name: str, params: dict) -> FakeRpcQuery:
        self.calls.append((function_name, params))
        return FakeRpcQuery(self.data)


QUESTIONS = [
    {
        "type": "true_false",
        "statement": "La fotosíntesis usa luz.",
        "expected_answer": None,
        "options": [
            {
                "option_text": "Verdadero",
                "is_correct": True,
                "option_order": 1,
            },
            {
                "option_text": "Falso",
                "is_correct": False,
                "option_order": 2,
            },
        ],
    }
]

PERSISTED_EXAM = {
    "exam_id": EXAM_ID,
    "notebook_id": NOTEBOOK_ID,
    "name": "Fotosíntesis",
    "description": None,
    "status": "active",
    "questions": [
        {
            "question_id": QUESTION_ID,
            "type": "true_false",
            "statement": "La fotosíntesis usa luz.",
            "question_order": 1,
            "options": [
                {
                    "option_id": OPTION_IDS[0],
                    "option_text": "Verdadero",
                    "option_order": 1,
                },
                {
                    "option_id": OPTION_IDS[1],
                    "option_text": "Falso",
                    "option_order": 2,
                },
            ],
        }
    ],
}


@pytest.mark.parametrize(
    "rpc_data",
    [PERSISTED_EXAM, [PERSISTED_EXAM]],
    ids=["json-object", "single-row-wrapper"],
)
def test_persist_exam_returns_database_ids_and_accepts_supabase_shapes(rpc_data) -> None:
    client = FakeClient(rpc_data)
    repository = RagGenerationRepository(client)

    result = asyncio.run(
        repository.persist_exam(
            actor_id=ACTOR_ID,
            notebook_id=NOTEBOOK_ID,
            name="Fotosíntesis",
            description=None,
            questions=QUESTIONS,
        )
    )

    assert result["exam_id"] == EXAM_ID
    assert result["questions"][0]["question_id"] == QUESTION_ID
    assert result["questions"][0]["options"][0]["option_id"] == OPTION_IDS[0]
    assert client.calls == [
        (
            "persist_generated_exam",
            {
                "p_actor_id": ACTOR_ID,
                "p_notebook_id": NOTEBOOK_ID,
                "p_name": "Fotosíntesis",
                "p_description": None,
                "p_questions": QUESTIONS,
            },
        )
    ]


@pytest.mark.parametrize(
    "mutation",
    [
        lambda result: result.pop("exam_id"),
        lambda result: result.update(questions=[]),
        lambda result: result["questions"][0].pop("question_id"),
        lambda result: result["questions"][0].update(options=[]),
        lambda result: result["questions"][0]["options"][0].pop("option_id"),
    ],
    ids=[
        "missing-exam-id",
        "missing-exam-question-link",
        "missing-question-id",
        "missing-question-options",
        "missing-option-id",
    ],
)
def test_persist_exam_rejects_incomplete_database_result(mutation) -> None:
    result = deepcopy(PERSISTED_EXAM)
    mutation(result)

    with pytest.raises(RepositoryError, match="persistir el examen"):
        asyncio.run(
            RagGenerationRepository(FakeClient(result)).persist_exam(
                actor_id=ACTOR_ID,
                notebook_id=NOTEBOOK_ID,
                name="Fotosíntesis",
                description=None,
                questions=QUESTIONS,
            )
        )
