from __future__ import annotations

from typing import Any

from app.core.exceptions import RepositoryError
from app.infra.repositories.base import BaseSupabaseRepository


class RagGenerationRepository(BaseSupabaseRepository):
    async def list_flashcards(
        self,
        *,
        actor_id: str,
        notebook_id: str,
        limit: int,
        offset: int,
    ) -> list[dict[str, Any]]:
        try:
            response = await self._execute(
                self.client.rpc(
                    "list_notebook_flashcards",
                    {
                        "p_actor_id": actor_id,
                        "p_notebook_id": notebook_id,
                        "p_limit": limit,
                        "p_offset": offset,
                    },
                )
            )
        except Exception as exc:
            raise RepositoryError("listar las flashcards") from exc
        if not isinstance(response.data, list):
            raise RepositoryError("listar las flashcards")
        return response.data

    async def persist_flashcards(
        self,
        *,
        actor_id: str,
        notebook_id: str,
        items: list[dict[str, str]],
    ) -> list[dict[str, Any]]:
        try:
            response = await self._execute(
                self.client.rpc(
                    "persist_generated_flashcards",
                    {
                        "p_actor_id": actor_id,
                        "p_notebook_id": notebook_id,
                        "p_items": items,
                    },
                )
            )
        except Exception as exc:
            raise RepositoryError("persistir las flashcards") from exc
        if not isinstance(response.data, list):
            raise RepositoryError("persistir las flashcards")
        return response.data

    async def persist_exam(
        self,
        *,
        actor_id: str,
        notebook_id: str,
        name: str,
        description: str | None,
        questions: list[dict[str, Any]],
    ) -> dict[str, Any]:
        try:
            response = await self._execute(
                self.client.rpc(
                    "persist_generated_exam",
                    {
                        "p_actor_id": actor_id,
                        "p_notebook_id": notebook_id,
                        "p_name": name,
                        "p_description": description,
                        "p_questions": questions,
                    },
                )
            )
        except Exception as exc:
            raise RepositoryError("persistir el examen") from exc
        if not isinstance(response.data, dict):
            raise RepositoryError("persistir el examen")
        return response.data

    async def record_server_activity(
        self,
        *,
        actor_id: str,
        notebook_id: str,
        activity_type: str,
        quantity: int,
        idempotency_key: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        try:
            await self._execute(
                self.client.rpc(
                    "record_server_learning_event",
                    {
                        "p_actor_id": actor_id,
                        "p_notebook_id": notebook_id,
                        "p_activity_type": activity_type,
                        "p_quantity": quantity,
                        "p_idempotency_key": idempotency_key,
                        "p_metadata": metadata or {},
                    },
                )
            )
        except Exception as exc:
            raise RepositoryError("registrar la actividad") from exc
