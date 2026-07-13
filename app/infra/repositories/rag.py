from __future__ import annotations

from typing import Any

from app.core.exceptions import RepositoryError
from app.infra.repositories.base import BaseSupabaseRepository


class NotebookAccessRepository(BaseSupabaseRepository):
    async def has_notebook_access(self, *, user_id: str, notebook_id: str) -> bool:
        try:
            personal_query = (
                self.client.table("personal_notebooks")
                .select("notebook_id")
                .eq("user_id", user_id)
                .eq("notebook_id", notebook_id)
                .limit(1)
            )
            personal = await self._execute(personal_query)
            if personal.data:
                return True

            member_query = (
                self.client.table("study_members")
                .select("member_id")
                .eq("user_id", user_id)
                .limit(1)
            )
            member = await self._execute(member_query)
            member_id = self._first(member.data or [])
            if not member_id:
                return False

            room_notebooks_query = (
                self.client.table("room_notebooks")
                .select("room_id")
                .eq("notebook_id", notebook_id)
            )
            room_notebooks = await self._execute(room_notebooks_query)
            room_ids = [item["room_id"] for item in room_notebooks.data or []]
            if not room_ids:
                return False

            membership_query = (
                self.client.table("members_rooms")
                .select("room_id")
                .eq("member_id", member_id["member_id"])
                .in_("room_id", room_ids)
                .limit(1)
            )
            membership = await self._execute(membership_query)
        except Exception as exc:
            raise RepositoryError("validar acceso") from exc
        return bool(membership.data)

    async def has_notebook_manage_access(
        self, *, user_id: str, notebook_id: str
    ) -> bool:
        try:
            personal_query = (
                self.client.table("personal_notebooks")
                .select("notebook_id")
                .eq("user_id", user_id)
                .eq("notebook_id", notebook_id)
                .limit(1)
            )
            personal = await self._execute(personal_query)
            if personal.data:
                return True

            member_query = (
                self.client.table("study_members")
                .select("member_id")
                .eq("user_id", user_id)
                .limit(1)
            )
            member = await self._execute(member_query)
            member_row = self._first(member.data or [])
            if member_row is None:
                return False

            room_query = (
                self.client.table("room_notebooks")
                .select("room_id")
                .eq("notebook_id", notebook_id)
            )
            rooms = await self._execute(room_query)
            room_ids = [row["room_id"] for row in rooms.data or []]
            if not room_ids:
                return False

            admin_query = (
                self.client.table("members_rooms")
                .select("room_id")
                .eq("member_id", member_row["member_id"])
                .eq("role", "admin")
                .in_("room_id", room_ids)
                .limit(1)
            )
            admin = await self._execute(admin_query)
        except Exception as exc:
            raise RepositoryError("validar permisos") from exc
        return bool(admin.data)


class ConversationRepository(BaseSupabaseRepository):
    async def create(
        self, *, notebook_id: str, user_id: str, name: str
    ) -> dict[str, Any]:
        return await self._create(
            "ai_conversations",
            {
                "notebook_id": notebook_id,
                "created_by_user_id": user_id,
                "name": name,
            },
        )

    async def list_by_notebook(
        self, *, notebook_id: str, user_id: str, limit: int, offset: int
    ) -> list[dict[str, Any]]:
        try:
            query = (
                self.client.table("ai_conversations")
                .select("*")
                .eq("notebook_id", notebook_id)
                .eq("created_by_user_id", user_id)
                .order("created_at", desc=True)
                .range(offset, offset + limit - 1)
            )
            response = await self._execute(query)
        except Exception as exc:
            raise RepositoryError("listar") from exc
        return response.data or []

    async def get(
        self, *, conversation_id: str, user_id: str
    ) -> dict[str, Any] | None:
        try:
            query = (
                self.client.table("ai_conversations")
                .select("*")
                .eq("conversation_id", conversation_id)
                .eq("created_by_user_id", user_id)
                .limit(1)
            )
            response = await self._execute(query)
        except Exception as exc:
            raise RepositoryError("consultar") from exc
        return self._first(response.data)

    async def list_messages(
        self, *, conversation_id: str, limit: int, offset: int
    ) -> list[dict[str, Any]]:
        try:
            query = (
                self.client.table("messages")
                .select("*")
                .eq("conversation_id", conversation_id)
                .order("order_message")
                .range(offset, offset + limit - 1)
            )
            response = await self._execute(query)
        except Exception as exc:
            raise RepositoryError("listar") from exc
        return response.data or []

    async def list_recent_messages(
        self, *, conversation_id: str, limit: int
    ) -> list[dict[str, Any]]:
        try:
            query = (
                self.client.table("messages")
                .select("role,content,order_message")
                .eq("conversation_id", conversation_id)
                .order("order_message", desc=True)
                .limit(limit)
            )
            response = await self._execute(query)
        except Exception as exc:
            raise RepositoryError("listar") from exc
        return list(reversed(response.data or []))

    async def next_message_order(self, *, conversation_id: str) -> int:
        try:
            query = (
                self.client.table("messages")
                .select("order_message")
                .eq("conversation_id", conversation_id)
                .order("order_message", desc=True)
                .limit(1)
            )
            response = await self._execute(query)
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
        actor_id: str,
        order_message: int | None = None,
        sent_by_user_id: str | None = None,
    ) -> dict[str, Any]:
        del order_message, sent_by_user_id
        return await self._rpc_first(
            "append_conversation_message",
            {
                "p_actor_id": actor_id,
                "p_conversation_id": conversation_id,
                "p_role": role,
                "p_content": content,
            },
            "guardar el mensaje",
        )


class RagSearchRepository(BaseSupabaseRepository):
    async def search_chunks(
        self, *, notebook_id: str, embedding: list[float], limit: int
    ) -> list[dict[str, Any]]:
        try:
            query = self.client.rpc(
                "match_document_chunks",
                {
                    "query_embedding": embedding,
                    "match_notebook_id": notebook_id,
                    "match_count": limit,
                },
            )
            response = await self._execute(query)
        except Exception as exc:
            raise RepositoryError("buscar contexto") from exc
        return response.data or []
