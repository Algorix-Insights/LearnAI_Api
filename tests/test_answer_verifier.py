from __future__ import annotations

import asyncio
import json

import pytest

from app.core.exceptions import BadRequestError
from app.infra.agents.answer_verifier import OpenRouterAnswerVerifier


class FakeLlm:
    def __init__(self, content: str) -> None:
        self.content = content
        self.payload: dict | None = None

    async def chat_completion(self, **kwargs):
        self.payload = kwargs
        return {"choices": [{"message": {"content": self.content}}]}


def test_open_answer_verifier_uses_strict_structured_output() -> None:
    llm = FakeLlm(
        json.dumps(
            {
                "is_correct": True,
                "confidence": 0.92,
                "feedback": "La respuesta conserva el concepto esencial.",
            }
        )
    )
    verifier = OpenRouterAnswerVerifier(llm, model="provider/model")

    result = asyncio.run(
        verifier.verify(
            question="¿Que es fotosintesis?",
            expected_answer="Proceso que convierte luz en energia quimica.",
            submitted_answer="Las plantas transforman luz en energia almacenada.",
        )
    )

    assert result.is_correct is True
    assert result.confidence == 0.92
    assert llm.payload is not None
    assert llm.payload["response_format"]["json_schema"]["strict"] is True


def test_open_answer_verifier_rejects_non_json_response() -> None:
    verifier = OpenRouterAnswerVerifier(FakeLlm("correcta"), model="provider/model")

    with pytest.raises(BadRequestError):
        asyncio.run(
            verifier.verify(
                question="Pregunta",
                expected_answer="Esperada",
                submitted_answer="Respuesta",
            )
        )
