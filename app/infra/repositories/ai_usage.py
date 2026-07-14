from __future__ import annotations

from app.core.exceptions import ApiError, BadRequestError, RepositoryError
from app.infra.repositories.base import BaseSupabaseRepository


class AiUsageRepository(BaseSupabaseRepository):
    async def reserve(
        self, *, actor_id: str, operation: str, units: int = 1
    ) -> None:
        try:
            await self._execute(
                self.client.rpc(
                    "reserve_ai_usage",
                    {
                        "p_actor_id": actor_id,
                        "p_operation": operation,
                        "p_units": units,
                    },
                )
            )
        except Exception as exc:
            message = " ".join(
                str(value)
                for value in (
                    getattr(exc, "message", ""),
                    getattr(exc, "code", ""),
                    exc,
                )
                if value
            ).casefold()
            if "ai_usage_rate_limit" in message:
                raise ApiError(
                    429,
                    "Alcanzaste el límite temporal de operaciones de IA.",
                    headers={"Retry-After": "0"},
                ) from exc
            if "invalid ai operation" in message or "invalid ai units" in message:
                raise BadRequestError("Operación de IA inválida.") from exc
            raise RepositoryError("reservar la operación de IA") from exc
