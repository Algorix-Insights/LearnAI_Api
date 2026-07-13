from __future__ import annotations

from typing import Any

from app.core.exceptions import RepositoryError
from app.infra.repositories.base import BaseSupabaseRepository


class RagGenerationRepository(BaseSupabaseRepository):
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
