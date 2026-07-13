from __future__ import annotations

import asyncio

from supabase import Client

from app.infra.db.supabase import get_supabase_admin_client


class SupabaseStorage:
    def __init__(self, client: Client | None = None) -> None:
        self.client = client or get_supabase_admin_client()

    async def upload(
        self,
        *,
        bucket: str,
        path: str,
        content: bytes,
        content_type: str,
        upsert: bool = True,
    ) -> str:
        await asyncio.to_thread(
            self.client.storage.from_(bucket).upload,
            path=path,
            file=content,
            file_options={
                "content-type": content_type,
                "upsert": str(upsert).lower(),
            },
        )
        return path

    async def public_url(self, *, bucket: str, path: str) -> str:
        return await asyncio.to_thread(
            self.client.storage.from_(bucket).get_public_url,
            path,
        )

    async def signed_url(
        self, *, bucket: str, path: str, expires_in: int = 3600
    ) -> str:
        result = await asyncio.to_thread(
            self.client.storage.from_(bucket).create_signed_url,
            path,
            expires_in,
        )
        if isinstance(result, dict):
            value = result.get("signedURL") or result.get("signedUrl")
            if isinstance(value, str) and value:
                return value
        value = getattr(result, "signed_url", None)
        if isinstance(value, str) and value:
            return value
        raise RuntimeError("Supabase Storage no devolvio una URL firmada.")

    async def delete(self, *, bucket: str, paths: list[str]) -> None:
        if not paths:
            return
        await asyncio.to_thread(
            self.client.storage.from_(bucket).remove,
            paths,
        )
