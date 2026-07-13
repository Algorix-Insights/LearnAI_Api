from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from app.core.exceptions import ForbiddenError
from app.infra.repositories.ai_usage import AiUsageRepository
from app.infra.repositories.rag import NotebookAccessRepository
from app.infra.repositories.rag_generation import RagGenerationRepository


logger = logging.getLogger("learnia.rag")


class RagAccessPolicy:
    """Centralizes actor authorization, durable quotas, and best-effort analytics."""

    def __init__(
        self,
        *,
        access: NotebookAccessRepository,
        usage: AiUsageRepository | None,
        generation: RagGenerationRepository | None,
    ) -> None:
        self.access = access
        self.usage = usage
        self.generation = generation

    async def require_access(self, *, user_id: UUID, notebook_id: UUID) -> None:
        allowed = await self.access.has_notebook_access(
            user_id=str(user_id), notebook_id=str(notebook_id)
        )
        if not allowed:
            raise ForbiddenError()

    async def require_manage_access(self, *, user_id: UUID, notebook_id: UUID) -> None:
        allowed = await self.access.has_notebook_manage_access(
            user_id=str(user_id), notebook_id=str(notebook_id)
        )
        if not allowed:
            raise ForbiddenError()

    async def reserve_ai_usage(self, user_id: UUID, operation: str) -> None:
        if self.usage is not None:
            await self.usage.reserve(actor_id=str(user_id), operation=operation)

    async def record_server_activity(
        self,
        *,
        actor_id: UUID,
        notebook_id: UUID,
        activity_type: str,
        quantity: int,
        idempotency_key: str,
        metadata: dict[str, Any],
    ) -> None:
        if self.generation is None:
            return
        try:
            await self.generation.record_server_activity(
                actor_id=str(actor_id),
                notebook_id=str(notebook_id),
                activity_type=activity_type,
                quantity=quantity,
                idempotency_key=idempotency_key,
                metadata=metadata,
            )
        except Exception:
            # The document already exists and is usable; an analytics outage
            # must not turn a successful upload into a duplicate-prone retry.
            logger.warning("learning_activity_record_failed", exc_info=True)
