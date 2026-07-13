from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import UploadFile

from app.core.config import Settings
from app.core.exceptions import BadRequestError, ResourceNotFoundError
from app.domain.interfaces import UserRepository
from app.domain.schemas.entities import UserUpdate
from app.domain.schemas.resources.user_profile import (
    ProfilePhotoDeleteResponse,
    ProfilePhotoResponse,
)
from app.domain.schemas.resources.users import (
    UserRepositoryGetRequest,
    UserRepositoryUpdateRequest,
)
from app.domain.services.rag import ProfileImageProcessor
from app.infra.storage import SupabaseStorage


class UserProfileUseCase:
    signed_url_ttl_seconds = 3600

    def __init__(
        self,
        users: UserRepository,
        storage: SupabaseStorage,
        settings: Settings,
        image_processor: ProfileImageProcessor | None = None,
    ) -> None:
        self.users = users
        self.storage = storage
        self.settings = settings
        self.image_processor = image_processor or ProfileImageProcessor()

    async def upload_photo(
        self, *, user_id: UUID, file: UploadFile
    ) -> ProfilePhotoResponse:
        user = await self._get_user(user_id)
        content, content_type = await self.image_processor.read_upload(file)
        path = self.image_processor.storage_path(user_id, content_type)
        previous_path = user.get("profile_image_path")
        await self.storage.upload(
            bucket=self.settings.profile_bucket,
            path=path,
            content=content,
            content_type=content_type,
            upsert=True,
        )
        updated = await self.users.update(
            UserRepositoryUpdateRequest(
                user_id=user_id,
                payload=UserUpdate(
                    profile_image_path=path,
                    profile_image_mime_type=content_type,
                    profile_image_size_bytes=len(content),
                ),
                updated_at=datetime.now(UTC),
            )
        )
        if updated is None:
            await self.storage.delete(bucket=self.settings.profile_bucket, paths=[path])
            raise ResourceNotFoundError()
        if previous_path and previous_path != path:
            await self.storage.delete(
                bucket=self.settings.profile_bucket, paths=[str(previous_path)]
            )
        return await self._response(user_id, updated)

    async def get_photo(self, *, user_id: UUID) -> ProfilePhotoResponse:
        user = await self._get_user(user_id)
        return await self._response(user_id, user)

    async def delete_photo(
        self, *, user_id: UUID
    ) -> ProfilePhotoDeleteResponse:
        user = await self._get_user(user_id)
        path = user.get("profile_image_path")
        if path:
            await self.storage.delete(
                bucket=self.settings.profile_bucket, paths=[str(path)]
            )
        updated = await self.users.update(
            UserRepositoryUpdateRequest(
                user_id=user_id,
                payload=UserUpdate(
                    profile_image_path=None,
                    profile_image_mime_type=None,
                    profile_image_size_bytes=None,
                ),
                updated_at=datetime.now(UTC),
            )
        )
        if updated is None:
            raise ResourceNotFoundError()
        return ProfilePhotoDeleteResponse(deleted=bool(path))

    async def _get_user(self, user_id: UUID) -> dict:
        user = await self.users.get(UserRepositoryGetRequest(user_id=user_id))
        if user is None:
            raise ResourceNotFoundError()
        return user

    async def _response(self, user_id: UUID, user: dict) -> ProfilePhotoResponse:
        path = user.get("profile_image_path")
        mime_type = user.get("profile_image_mime_type")
        size_bytes = user.get("profile_image_size_bytes")
        if not path or not mime_type or size_bytes is None:
            raise ResourceNotFoundError()
        try:
            url = await self.storage.signed_url(
                bucket=self.settings.profile_bucket,
                path=str(path),
                expires_in=self.signed_url_ttl_seconds,
            )
        except Exception as exc:
            raise BadRequestError("No se pudo generar la URL de la foto de perfil.") from exc
        return ProfilePhotoResponse(
            data={
                "user_id": user_id,
                "storage_path": str(path),
                "mime_type": str(mime_type),
                "size_bytes": int(size_bytes),
                "url": url,
                "expires_in": self.signed_url_ttl_seconds,
            }
        )
