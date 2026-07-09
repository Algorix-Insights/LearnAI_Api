from __future__ import annotations

import asyncio
from typing import Any
from uuid import UUID

from fastapi import UploadFile

from app.application.usecases.rag import RagUseCase
from app.core.config import Settings
from app.domain.schemas.resources.rag import ChatRequest
from app.domain.services.rag import RagDocumentProcessor


NOTEBOOK_ID = UUID("00000000-0000-0000-0000-000000000010")
USER_ID = UUID("00000000-0000-0000-0000-000000000020")
CONVERSATION_ID = UUID("00000000-0000-0000-0000-000000000030")


def run_async(coro):
    return asyncio.run(coro)


class FakeDocuments:
    def __init__(self) -> None:
        self.items: dict[str, dict[str, Any]] = {}

    async def get_by_hash(self, *, notebook_id: str, content_hash: str) -> dict | None:
        for item in self.items.values():
            if item["notebook_id"] == notebook_id and item["content_hash"] == content_hash:
                return item
        return None

    async def create(self, request) -> dict:
        payload = request.payload.model_dump(mode="json")
        item = {
            "document_id": "00000000-0000-0000-0000-000000000040",
            **payload,
        }
        self.items[item["document_id"]] = item
        return item

    async def update(self, request) -> dict | None:
        item = self.items.get(str(request.document_id))
        if item is None:
            return None
        item.update(request.payload.model_dump(exclude_unset=True, mode="json"))
        return item


class FakeChunks:
    def __init__(self) -> None:
        self.items: list[dict[str, Any]] = []

    async def create_many(self, payloads: list[dict]) -> list[dict]:
        self.items.extend(payloads)
        return payloads

    async def count_for_document(self, document_id: str) -> int:
        return len([item for item in self.items if item["document_id"] == document_id])


class FakeConversations:
    def __init__(self) -> None:
        self.messages: list[dict[str, Any]] = []

    async def create(self, *, notebook_id: str, name: str) -> dict:
        return {
            "conversation_id": str(CONVERSATION_ID),
            "notebook_id": notebook_id,
            "name": name,
        }

    async def list_by_notebook(self, *, notebook_id: str, limit: int, offset: int) -> list[dict]:
        return []

    async def get(self, *, conversation_id: str) -> dict | None:
        return {"conversation_id": conversation_id, "notebook_id": str(NOTEBOOK_ID)}

    async def list_messages(self, *, conversation_id: str, limit: int, offset: int) -> list[dict]:
        return self.messages[offset : offset + limit]

    async def next_message_order(self, *, conversation_id: str) -> int:
        return len(self.messages) + 1

    async def create_message(
        self,
        *,
        conversation_id: str,
        role: str,
        content: str,
        order_message: int,
        sent_by_user_id: str | None = None,
    ) -> dict:
        item = {
            "message_id": f"00000000-0000-0000-0000-00000000006{order_message}",
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "order_message": order_message,
            "sent_by_user_id": sent_by_user_id,
        }
        self.messages.append(item)
        return item


class FakeSearch:
    async def search_chunks(self, *, notebook_id: str, embedding: list[float], limit: int) -> list[dict]:
        return [
            {
                "chunk_id": "00000000-0000-0000-0000-000000000050",
                "document_id": "00000000-0000-0000-0000-000000000040",
                "document_name": "notas.md",
                "content": "La fotosintesis usa luz.",
                "similarity": 0.9,
            }
        ]


class FakeAccess:
    async def has_notebook_access(self, *, user_id: str, notebook_id: str) -> bool:
        return True


class FakeUsers:
    pass


class FakeStorage:
    def __init__(self) -> None:
        self.uploads: list[dict[str, Any]] = []

    async def upload(
        self,
        *,
        bucket: str,
        path: str,
        content: bytes,
        content_type: str,
        upsert: bool = True,
    ) -> str:
        self.uploads.append(
            {
                "bucket": bucket,
                "path": path,
                "content": content,
                "content_type": content_type,
                "upsert": upsert,
            }
        )
        return path


class FakeLlm:
    async def embeddings(self, *, model: str, input, **params) -> dict:
        items = input if isinstance(input, list) else [input]
        return {"data": [{"embedding": [0.1] * 1536} for _ in items]}

    async def chat_completion(self, *, messages, model=None, stream=False, **params) -> dict:
        return {"choices": [{"message": {"content": "La fotosintesis usa luz. [1]"}}]}


def make_use_case() -> tuple[RagUseCase, FakeStorage, FakeChunks, FakeConversations]:
    storage = FakeStorage()
    chunks = FakeChunks()
    conversations = FakeConversations()
    use_case = RagUseCase(
        documents=FakeDocuments(),
        chunks=chunks,
        conversations=conversations,
        search=FakeSearch(),
        access=FakeAccess(),
        users=FakeUsers(),
        storage=storage,
        llm=FakeLlm(),
        settings=Settings(openrouter_api_key="test-key"),
    )
    return use_case, storage, chunks, conversations


def upload_file(name: str, content: bytes, content_type: str) -> UploadFile:
    from io import BytesIO

    return UploadFile(filename=name, file=BytesIO(content), headers={"content-type": content_type})


def test_rag_upload_vectorizes_markdown_document() -> None:
    use_case, storage, chunks, _ = make_use_case()

    response = run_async(
        use_case.upload_document(
            notebook_id=NOTEBOOK_ID,
            user_id=USER_ID,
            file=upload_file("notas.md", b"# Fotosintesis\nUsa luz.", "text/markdown"),
        )
    )

    assert response.data.processing_status == "completed"
    assert response.data.chunks_count == 1
    assert storage.uploads[0]["bucket"] == "documents"
    assert chunks.items[0]["model"] == "openai/text-embedding-3-small"
    assert len(chunks.items[0]["embedding"]) == 1536


def test_rag_chat_uses_retrieved_sources_and_stores_messages() -> None:
    use_case, _, _, conversations = make_use_case()

    response = run_async(
        use_case.chat(
            conversation_id=CONVERSATION_ID,
            request=ChatRequest(user_id=USER_ID, content="Que usa la fotosintesis?"),
        )
    )

    assert response.data.role == "assistant"
    assert response.sources[0].document_name == "notas.md"
    assert [message["role"] for message in conversations.messages] == ["user", "assistant"]


def test_rag_processor_rejects_unsupported_documents() -> None:
    processor = RagDocumentProcessor()

    async def read_invalid():
        return await processor.read_upload(upload_file("image.png", b"x", "image/png"))

    try:
        run_async(read_invalid())
    except Exception as exc:
        assert "Solo se permiten" in str(exc)
    else:
        raise AssertionError("unsupported file accepted")
