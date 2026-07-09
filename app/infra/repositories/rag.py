from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.core.exceptions import RepositoryError
from app.infra.repositories.base import BaseSupabaseRepository


class NotebookAccessRepository(BaseSupabaseRepository):
    async def has_notebook_access(self, *, user_id: str, notebook_id: str) -> bool:
        try:
            personal = (
                self.client.table("personal_notebooks")
                .select("notebook_id")
                .eq("user_id", user_id)
                .eq("notebook_id", notebook_id)
                .limit(1)
                .execute()
            )
            if personal.data:
                return True

            member = (
                self.client.table("study_members")
                .select("member_id")
                .eq("user_id", user_id)
                .limit(1)
                .execute()
            )
            member_id = self._first(member.data or [])
            if not member_id:
                return False

            room_notebooks = (
                self.client.table("room_notebooks")
                .select("room_id")
                .eq("notebook_id", notebook_id)
                .execute()
            )
            room_ids = [item["room_id"] for item in room_notebooks.data or []]
            if not room_ids:
                return False

            membership = (
                self.client.table("members_rooms")
                .select("room_id")
                .eq("member_id", member_id["member_id"])
                .in_("room_id", room_ids)
                .limit(1)
                .execute()
            )
        except Exception as exc:
            raise RepositoryError("validar acceso") from exc
        return bool(membership.data)


class ConversationRepository(BaseSupabaseRepository):
    async def create(self, *, notebook_id: str, name: str) -> dict[str, Any]:
        return await self._create(
            "ai_conversations",
            {"notebook_id": notebook_id, "name": name},
        )

    async def list_by_notebook(
        self, *, notebook_id: str, limit: int, offset: int
    ) -> list[dict[str, Any]]:
        try:
            response = (
                self.client.table("ai_conversations")
                .select("*")
                .eq("notebook_id", notebook_id)
                .order("created_at", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )
        except Exception as exc:
            raise RepositoryError("listar") from exc
        return response.data or []

    async def get(self, *, conversation_id: str) -> dict[str, Any] | None:
        return await self._get("ai_conversations", "conversation_id", conversation_id)

    async def list_messages(
        self, *, conversation_id: str, limit: int, offset: int
    ) -> list[dict[str, Any]]:
        try:
            response = (
                self.client.table("messages")
                .select("*")
                .eq("conversation_id", conversation_id)
                .order("order_message")
                .range(offset, offset + limit - 1)
                .execute()
            )
        except Exception as exc:
            raise RepositoryError("listar") from exc
        return response.data or []

    async def next_message_order(self, *, conversation_id: str) -> int:
        try:
            response = (
                self.client.table("messages")
                .select("order_message")
                .eq("conversation_id", conversation_id)
                .order("order_message", desc=True)
                .limit(1)
                .execute()
            )
        except Exception as exc:
            raise RepositoryError("consultar") from exc
        current = self._first(response.data or [])
        return int(current["order_message"]) + 1 if current else 1

    async def create_message(
        self,
        *,
        conversation_id: str,
        role: str,
        content: str,
        order_message: int,
        sent_by_user_id: str | None = None,
    ) -> dict[str, Any]:
        payload = {
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "order_message": order_message,
        }
        if sent_by_user_id is not None:
            payload["sent_by_user_id"] = sent_by_user_id
        data = await self._create("messages", payload)
        await self._update(
            "ai_conversations",
            "conversation_id",
            conversation_id,
            {"updated_at": datetime.now(UTC).isoformat()},
        )
        return data


class RagSearchRepository(BaseSupabaseRepository):
    async def search_chunks(
        self, *, notebook_id: str, embedding: list[float], limit: int
    ) -> list[dict[str, Any]]:
        try:
            response = self.client.rpc(
                "match_document_chunks",
                {
                    "query_embedding": embedding,
                    "match_notebook_id": notebook_id,
                    "match_count": limit,
                },
            ).execute()
        except Exception as exc:
            raise RepositoryError("buscar contexto") from exc
        return response.data or []
