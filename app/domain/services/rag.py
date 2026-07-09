from __future__ import annotations

from hashlib import sha256
from io import BytesIO
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile

from app.core.exceptions import BadRequestError


class RagDocumentProcessor:
    allowed_extensions = {".pdf", ".txt", ".md"}
    source_types = {".pdf": "pdf", ".txt": "txt", ".md": "markdown"}

    async def read_upload(self, file: UploadFile) -> tuple[bytes, str, str]:
        filename = file.filename or ""
        suffix = Path(filename).suffix.lower()
        if suffix not in self.allowed_extensions:
            raise BadRequestError("Solo se permiten archivos pdf, txt y md.")
        content = await file.read()
        if not content:
            raise BadRequestError("El archivo esta vacio.")
        content_type = file.content_type or self._default_mime_type(suffix)
        return content, suffix, content_type

    def storage_path(self, notebook_id: UUID, filename: str, suffix: str) -> str:
        safe_name = Path(filename or f"document{suffix}").name.replace(" ", "_")
        return f"{notebook_id}/{uuid4()}-{safe_name}"

    def content_hash(self, content: bytes) -> str:
        return sha256(content).hexdigest()

    def source_type(self, suffix: str) -> str:
        return self.source_types[suffix]

    def extract_text(self, content: bytes, suffix: str) -> str:
        if suffix == ".pdf":
            text = self._extract_pdf_text(content)
        else:
            text = content.decode("utf-8", errors="ignore")
        text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
        if not text:
            raise BadRequestError("No se pudo extraer texto del archivo.")
        return text

    def chunk_text(self, text: str, *, chunk_size: int = 3500, overlap: int = 300) -> list[str]:
        chunks: list[str] = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end == len(text):
                break
            start = max(end - overlap, start + 1)
        return chunks

    def _extract_pdf_text(self, content: bytes) -> str:
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise BadRequestError("Dependencia pypdf no instalada.") from exc
        reader = PdfReader(BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    def _default_mime_type(self, suffix: str) -> str:
        if suffix == ".pdf":
            return "application/pdf"
        if suffix == ".md":
            return "text/markdown"
        return "text/plain"


class ProfileImageProcessor:
    allowed_mime_types = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    extensions = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/gif": ".gif",
    }

    async def read_upload(self, file: UploadFile) -> tuple[bytes, str]:
        content_type = file.content_type or ""
        if content_type not in self.allowed_mime_types:
            raise BadRequestError("Solo se permiten imagenes jpeg, png, webp o gif.")
        content = await file.read()
        if not content:
            raise BadRequestError("La imagen esta vacia.")
        return content, content_type

    def storage_path(self, user_id: UUID, content_type: str) -> str:
        return f"{user_id}/profile{self.extensions[content_type]}"
