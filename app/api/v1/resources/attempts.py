from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user, get_exam_attempt_workflow_use_case
from app.application.usecases.exam_attempts import ExamAttemptWorkflowUseCase
from app.core.exceptions import UnauthorizedError
from app.domain.schemas.resources.attempts import (
    AttemptSessionResponse,
    FinishAttemptRequest,
    FinishedAttemptResponse,
    SubmitAttemptAnswerRequest,
    SubmittedAttemptAnswerResponse,
)
from app.domain.schemas.resources.users import UserRead

router = APIRouter(prefix="/attempts", tags=["exam-attempts"])


@router.get("/{attempt_id}", response_model=AttemptSessionResponse)
async def get_attempt_session(
    attempt_id: UUID,
    current_user: Annotated[UserRead, Depends(get_current_user)],
    use_case: Annotated[
        ExamAttemptWorkflowUseCase, Depends(get_exam_attempt_workflow_use_case)
    ],
) -> AttemptSessionResponse:
    return await use_case.get_session(
        attempt_id=attempt_id,
        user_id=_current_user_id(current_user),
    )


@router.put(
    "/{attempt_id}/answers/{question_id}",
    response_model=SubmittedAttemptAnswerResponse,
)
async def submit_attempt_answer(
    attempt_id: UUID,
    question_id: UUID,
    payload: SubmitAttemptAnswerRequest,
    current_user: Annotated[UserRead, Depends(get_current_user)],
    use_case: Annotated[
        ExamAttemptWorkflowUseCase, Depends(get_exam_attempt_workflow_use_case)
    ],
) -> SubmittedAttemptAnswerResponse:
    return await use_case.submit_answer(
        attempt_id=attempt_id,
        question_id=question_id,
        user_id=_current_user_id(current_user),
        request=payload,
    )


@router.post("/{attempt_id}/finish", response_model=FinishedAttemptResponse)
async def finish_attempt(
    attempt_id: UUID,
    _payload: FinishAttemptRequest,
    current_user: Annotated[UserRead, Depends(get_current_user)],
    use_case: Annotated[
        ExamAttemptWorkflowUseCase, Depends(get_exam_attempt_workflow_use_case)
    ],
) -> FinishedAttemptResponse:
    return await use_case.finish(
        attempt_id=attempt_id,
        user_id=_current_user_id(current_user),
    )


def _current_user_id(current_user: UserRead) -> UUID:
    if current_user.user_id is None:
        raise UnauthorizedError()
    return current_user.user_id
