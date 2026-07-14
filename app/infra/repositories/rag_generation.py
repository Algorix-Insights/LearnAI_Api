from __future__ import annotations

from typing import Any
from uuid import UUID

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
        data = await self._rpc_first(
            "persist_generated_exam",
            {
                "p_actor_id": actor_id,
                "p_notebook_id": notebook_id,
                "p_name": name,
                "p_description": description,
                "p_questions": questions,
            },
            "persistir el examen",
        )
        self._validate_persisted_exam(
            data,
            notebook_id=notebook_id,
            questions=questions,
        )
        return data

    @staticmethod
    def _validate_persisted_exam(
        data: dict[str, Any],
        *,
        notebook_id: str,
        questions: list[dict[str, Any]],
    ) -> None:
        try:
            UUID(str(data["exam_id"]))
            persisted_notebook_id = UUID(str(data["notebook_id"]))
            expected_notebook_id = UUID(notebook_id)
            persisted_questions = data["questions"]
            if persisted_notebook_id != expected_notebook_id:
                raise ValueError
            if not isinstance(persisted_questions, list):
                raise TypeError
            if len(persisted_questions) != len(questions):
                raise ValueError

            for order, (persisted, expected) in enumerate(
                zip(persisted_questions, questions, strict=True),
                start=1,
            ):
                if not isinstance(persisted, dict):
                    raise TypeError
                UUID(str(persisted["question_id"]))
                if persisted.get("question_order") != order:
                    raise ValueError

                persisted_options = persisted.get("options")
                expected_options = expected.get("options")
                if not isinstance(persisted_options, list):
                    raise TypeError
                if not isinstance(expected_options, list):
                    raise TypeError
                if len(persisted_options) != len(expected_options):
                    raise ValueError

                for option_order, option in enumerate(persisted_options, start=1):
                    if not isinstance(option, dict):
                        raise TypeError
                    UUID(str(option["option_id"]))
                    if option.get("option_order") != option_order:
                        raise ValueError
        except (KeyError, TypeError, ValueError) as exc:
            raise RepositoryError("persistir el examen") from exc

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
