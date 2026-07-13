from __future__ import annotations

import asyncio
from io import BytesIO
from typing import Any
from uuid import UUID

from fastapi import UploadFile
import pytest

from app.application.usecases.user_profile import UserProfileUseCase
from app.core.config import Settings
from app.core.exceptions import BadRequestError
from app.domain.services.rag import ProfileImageProcessor


USER_ID = UUID("00000000-0000-0000-0000-000000000001")


class FakeUsers:
    def __init__(self) -> None:
        self.user: dict[str, Any] = {
            "user_id": str(USER_ID),
            "name": "Tym",
            "profile_image_path": "old/profile.png",
            "profile_image_mime_type": "image/png",
            "profile_image_size_bytes": 3,
        }

    async def get(self, request) -> dict[str, Any] | None:
        return self.user if request.user_id == USER_ID else None

    async def update(self, request) -> dict[str, Any] | None:
        self.user.update(request.payload.model_dump(exclude_unset=True, mode="json"))
        return self.user


class FakeStorage:
    def __init__(self) -> None:
        self.uploads: list[str] = []
        self.deleted: list[str] = []

    async def upload(self, *, bucket, path, content, content_type, upsert=True) -> str:
        self.uploads.append(path)
        return path

    async def signed_url(self, *, bucket, path, expires_in=3600) -> str:
        return f"https://signed.example/{bucket}/{path}"

    async def delete(self, *, bucket, paths) -> None:
        self.deleted.extend(paths)


class FakeImageProcessor:
    async def read_upload(self, file: UploadFile) -> tuple[bytes, str]:
        return await file.read(), "image/jpeg"

    def storage_path(self, user_id: UUID, content_type: str) -> str:
        return f"{user_id}/profile.jpg"


def test_profile_photo_upload_uses_current_user_and_cleans_previous_file() -> None:
    users = FakeUsers()
    storage = FakeStorage()
    use_case = UserProfileUseCase(
        users,
        storage,
        Settings(),
        image_processor=FakeImageProcessor(),
    )
    file = UploadFile(
        filename="avatar.jpg",
        file=BytesIO(b"jpeg"),
        headers={"content-type": "image/jpeg"},
    )

    response = asyncio.run(use_case.upload_photo(user_id=USER_ID, file=file))

    assert response.data.user_id == USER_ID
    assert response.data.mime_type == "image/jpeg"
    assert response.data.url.startswith("https://signed.example/")
    assert storage.uploads == [f"{USER_ID}/profile.jpg"]
    assert storage.deleted == ["old/profile.png"]


def test_profile_photo_delete_removes_storage_and_metadata() -> None:
    users = FakeUsers()
    storage = FakeStorage()
    use_case = UserProfileUseCase(users, storage, Settings())

    response = asyncio.run(use_case.delete_photo(user_id=USER_ID))

    assert response.deleted is True
    assert storage.deleted == ["old/profile.png"]
    assert users.user["profile_image_path"] is None


def test_profile_image_processor_uses_magic_bytes_not_only_claimed_mime() -> None:
    processor = ProfileImageProcessor()
    spoofed = UploadFile(
        filename="payload.png",
        file=BytesIO(b"not-an-image"),
        headers={"content-type": "image/png"},
    )

    with pytest.raises(BadRequestError):
        asyncio.run(processor.read_upload(spoofed))

    valid_png = UploadFile(
        filename="avatar.png",
        file=BytesIO(b"\x89PNG\r\n\x1a\nrest"),
        headers={"content-type": "image/png"},
    )
    content, content_type = asyncio.run(processor.read_upload(valid_png))

    assert content.startswith(b"\x89PNG")
    assert content_type == "image/png"
