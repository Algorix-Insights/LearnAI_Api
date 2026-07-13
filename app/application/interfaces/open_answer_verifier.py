from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class OpenAnswerVerification:
    is_correct: bool
    confidence: float | None = None
    feedback: str | None = None


class OpenAnswerVerifier(Protocol):
    async def verify(
        self,
        *,
        question: str,
        expected_answer: str,
        submitted_answer: str,
    ) -> OpenAnswerVerification:
        raise NotImplementedError
