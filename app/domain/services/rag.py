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
    max_size_bytes = 10 * 1024 * 1024
    max_pdf_pages = 200

    async def read_upload(self, file: UploadFile) -> tuple[bytes, str, str]:
        filename = file.filename or ""
        suffix = Path(filename).suffix.lower()
        if suffix not in self.allowed_extensions:
            raise BadRequestError("Solo se permiten archivos pdf, txt y md.")
        content = await file.read(self.max_size_bytes + 1)
        if not content:
            raise BadRequestError("El archivo esta vacio.")
        if len(content) > self.max_size_bytes:
            raise BadRequestError("El archivo excede el limite de 10 MB.")
        if suffix == ".pdf" and not content.startswith(b"%PDF-"):
            raise BadRequestError("El contenido no corresponde a un PDF valido.")
        if suffix in {".txt", ".md"} and b"\x00" in content:
            raise BadRequestError("El archivo de texto contiene datos binarios.")
        content_type = self._default_mime_type(suffix)
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
        if len(reader.pages) > self.max_pdf_pages:
            raise BadRequestError("El PDF excede el limite de 200 paginas.")
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
    max_size_bytes = 5 * 1024 * 1024

    async def read_upload(self, file: UploadFile) -> tuple[bytes, str]:
        content = await file.read(self.max_size_bytes + 1)
        if not content:
            raise BadRequestError("La imagen esta vacia.")
        if len(content) > self.max_size_bytes:
            raise BadRequestError("La imagen excede el limite de 5 MB.")
        detected_type = self._detect_mime_type(content)
        declared_type = file.content_type or ""
        if detected_type is None or (
            declared_type and declared_type != detected_type
        ):
            raise BadRequestError("El contenido no corresponde a una imagen permitida.")
        return content, detected_type

    def storage_path(self, user_id: UUID, content_type: str) -> str:
        return f"{user_id}/profile-{uuid4()}{self.extensions[content_type]}"

    def _detect_mime_type(self, content: bytes) -> str | None:
        if content.startswith(b"\xff\xd8\xff"):
            return "image/jpeg"
        if content.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png"
        if content.startswith((b"GIF87a", b"GIF89a")):
            return "image/gif"
        if len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP":
            return "image/webp"
        return None
