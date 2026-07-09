from __future__ import annotations

import asyncio

from supabase import Client

from app.infra.db.supabase import get_supabase_client


class SupabaseStorage:
    def __init__(self, client: Client | None = None) -> None:
        self.client = client or get_supabase_client()

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
