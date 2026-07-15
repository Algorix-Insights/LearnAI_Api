from __future__ import annotations

import asyncio
import json
from typing import Any
from uuid import UUID

from fastapi import UploadFile
import pytest
from pydantic import ValidationError

from app.application.usecases.rag import RagUseCase
from app.application.usecases.rag_support.study_materials import RagStudyMaterialWorkflow
from app.core.config import Settings
from app.core.exceptions import BadRequestError, ForbiddenError
from app.domain.schemas.resources.rag import (
    ChatRequest,
    ExamGenerationRequest,
    FlashcardGenerationRequest,
)
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

    async def delete(self, request) -> dict | None:
        return self.items.pop(str(request.document_id), None)


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

    async def create(self, *, notebook_id: str, user_id: str, name: str) -> dict:
        return {
            "conversation_id": str(CONVERSATION_ID),
            "notebook_id": notebook_id,
            "created_by_user_id": user_id,
            "name": name,
        }

    async def list_by_notebook(
        self, *, notebook_id: str, user_id: str, limit: int, offset: int
    ) -> list[dict]:
        return []

    async def get(self, *, conversation_id: str, user_id: str) -> dict | None:
        return {
            "conversation_id": conversation_id,
            "notebook_id": str(NOTEBOOK_ID),
            "created_by_user_id": user_id,
        }

    async def list_messages(self, *, conversation_id: str, limit: int, offset: int) -> list[dict]:
        return self.messages[offset : offset + limit]

    async def list_recent_messages(self, *, conversation_id: str, limit: int) -> list[dict]:
        return self.messages[-limit:]

    async def next_message_order(self, *, conversation_id: str) -> int:
        return len(self.messages) + 1

    async def create_message(
        self,
        *,
        conversation_id: str,
        role: str,
        content: str,
        actor_id: str,
        order_message: int | None = None,
        sent_by_user_id: str | None = None,
    ) -> dict:
        del actor_id
        order_message = order_message or len(self.messages) + 1
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
    def __init__(self, *, can_manage: bool = True) -> None:
        self.can_manage = can_manage

    async def has_notebook_access(self, *, user_id: str, notebook_id: str) -> bool:
        return True

    async def has_notebook_manage_access(
        self, *, user_id: str, notebook_id: str
    ) -> bool:
        return self.can_manage


class FakeQuestions:
    def __init__(self) -> None:
        self.items: list[dict[str, Any]] = []

    async def create(self, request) -> dict[str, Any]:
        payload = request.payload.model_dump(mode="json")
        item = {
            "question_id": f"10000000-0000-0000-0000-{len(self.items) + 1:012d}",
            **payload,
        }
        self.items.append(item)
        return item


class FakeFlashcards:
    def __init__(self) -> None:
        self.items: list[dict[str, Any]] = []

    async def create(self, request) -> dict[str, Any]:
        payload = request.payload.model_dump(mode="json")
        item = {
            "flashcard_id": f"20000000-0000-0000-0000-{len(self.items) + 1:012d}",
            **payload,
        }
        self.items.append(item)
        return item


class FakeExams:
    def __init__(self) -> None:
        self.items: list[dict[str, Any]] = []

    async def create(self, request) -> dict[str, Any]:
        payload = request.payload.model_dump(mode="json")
        item = {
            "exam_id": "30000000-0000-0000-0000-000000000001",
            **payload,
        }
        self.items.append(item)
        return item


class FakeExamQuestions:
    def __init__(self) -> None:
        self.items: list[dict[str, Any]] = []

    async def create(self, request) -> dict[str, Any]:
        item = request.model_dump(mode="json")
        self.items.append(item)
        return item


class FakeQuestionOptions:
    def __init__(self) -> None:
        self.items: list[dict[str, Any]] = []

    async def create(self, request) -> dict[str, Any]:
        payload = request.payload.model_dump(mode="json")
        item = {
            "option_id": f"40000000-0000-0000-0000-{len(self.items) + 1:012d}",
            **payload,
        }
        self.items.append(item)
        return item


class FakeStorage:
    def __init__(self) -> None:
        self.uploads: list[dict[str, Any]] = []
        self.deleted: list[str] = []

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

    async def delete(self, *, bucket: str, paths: list[str]) -> None:
        del bucket
        self.deleted.extend(paths)


class FakeLlm:
    def __init__(self, structured_responses: list[dict[str, Any] | str] | None = None) -> None:
        self.structured_responses = list(structured_responses or [])
        self.chat_payloads: list[dict[str, Any]] = []
        self.embedding_calls: list[list[str]] = []

    async def embeddings(self, *, model: str, input, **params) -> dict:
        items = input if isinstance(input, list) else [input]
        self.embedding_calls.append(items)
        return {"data": [{"embedding": [0.1] * 1536} for _ in items]}

    async def chat_completion(self, *, messages, model=None, stream=False, **params) -> dict:
        self.chat_payloads.append({"messages": messages, "model": model, **params})
        if "response_format" in params:
            content = self.structured_responses.pop(0)
            if not isinstance(content, str):
                content = json.dumps(content)
            return {"choices": [{"message": {"content": content}}]}
        return {"choices": [{"message": {"content": "La fotosintesis usa luz. [1]"}}]}


class FakeGeneration:
    def __init__(self) -> None:
        self.exam_calls: list[dict[str, Any]] = []

    async def list_flashcards(
        self, *, actor_id: str, notebook_id: str, limit: int, offset: int
    ) -> list[dict[str, Any]]:
        del actor_id
        return [
            {
                "flashcard_id": "20000000-0000-0000-0000-000000000001",
                "question_id": "10000000-0000-0000-0000-000000000001",
                "notebook_id": notebook_id,
                "question": "¿Qué usa la fotosíntesis?",
                "answer": "Luz.",
                "spent_time": 0,
            }
        ][offset : offset + limit]

    async def persist_exam(
        self,
        *,
        actor_id: str,
        notebook_id: str,
        name: str,
        description: str | None,
        questions: list[dict[str, Any]],
    ) -> dict[str, Any]:
        self.exam_calls.append(
            {
                "actor_id": actor_id,
                "notebook_id": notebook_id,
                "name": name,
                "description": description,
                "questions": questions,
            }
        )
        persisted_questions = []
        option_number = 0
        for question_order, question in enumerate(questions, start=1):
            persisted_options = []
            for option in question["options"]:
                option_number += 1
                persisted_options.append(
                    {
                        "option_id": (
                            f"40000000-0000-0000-0000-{option_number:012d}"
                        ),
                        "option_text": option["option_text"],
                        "option_order": option["option_order"],
                    }
                )
            persisted_questions.append(
                {
                    "question_id": (
                        f"10000000-0000-0000-0000-{question_order:012d}"
                    ),
                    "type": question["type"],
                    "statement": question["statement"],
                    "question_order": question_order,
                    "options": persisted_options,
                }
            )
        return {
            "exam_id": "30000000-0000-0000-0000-000000000001",
            "notebook_id": notebook_id,
            "name": name,
            "description": description,
            "status": "active",
            "questions": persisted_questions,
        }


class FakeUsage:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def reserve(
        self, *, actor_id: str, operation: str, units: int = 1
    ) -> None:
        self.calls.append(
            {"actor_id": actor_id, "operation": operation, "units": units}
        )


class ExplodingDocumentProcessor(RagDocumentProcessor):
    def extract_text(self, content: bytes, suffix: str) -> str:
        del content, suffix
        raise BadRequestError("documento malformado")


def make_use_case(
    llm: FakeLlm | None = None,
    generation=None,
    usage=None,
    document_processor: RagDocumentProcessor | None = None,
    access: FakeAccess | None = None,
) -> tuple[RagUseCase, FakeStorage, FakeChunks, FakeConversations]:
    storage = FakeStorage()
    chunks = FakeChunks()
    conversations = FakeConversations()
    use_case = RagUseCase(
        documents=FakeDocuments(),
        chunks=chunks,
        conversations=conversations,
        exams=FakeExams(),
        exam_questions=FakeExamQuestions(),
        questions=FakeQuestions(),
        question_options=FakeQuestionOptions(),
        flashcards=FakeFlashcards(),
        search=FakeSearch(),
        access=access or FakeAccess(),
        storage=storage,
        llm=llm or FakeLlm(),
        settings=Settings(openrouter_api_key="test-key"),
        generation=generation,
        usage=usage,
        document_processor=document_processor,
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
    serialized = response.model_dump(mode="json")
    assert "content_text" not in str(serialized)
    assert "content_hash" not in str(serialized)
    assert "storage_path" not in str(serialized)


def test_rag_chat_uses_retrieved_sources_and_stores_messages() -> None:
    llm = FakeLlm()
    use_case, _, _, conversations = make_use_case(llm)

    response = run_async(
        use_case.chat(
            conversation_id=CONVERSATION_ID,
            user_id=USER_ID,
            request=ChatRequest(content="Que usa la fotosintesis?"),
        )
    )

    assert response.data.role == "assistant"
    assert response.sources[0].document_name == "notas.md"
    assert [message["role"] for message in conversations.messages] == ["user", "assistant"]

    run_async(
        use_case.chat(
            conversation_id=CONVERSATION_ID,
            user_id=USER_ID,
            request=ChatRequest(content="¿Y para qué la usa?"),
        )
    )
    second_roles = [message["role"] for message in llm.chat_payloads[1]["messages"]]
    assert second_roles == ["system", "system", "user", "assistant", "user"]


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


def test_rag_request_schemas_reject_client_supplied_user_id() -> None:
    with pytest.raises(ValidationError):
        ChatRequest.model_validate(
            {"user_id": str(USER_ID), "content": "contenido del usuario"}
        )


def test_rag_rejects_oversized_document_before_reading() -> None:
    use_case, storage, _, _ = make_use_case()
    file = upload_file("grande.txt", b"contenido", "text/plain")
    file.size = 10 * 1024 * 1024 + 1

    with pytest.raises(BadRequestError, match="10 MB"):
        run_async(
            use_case.upload_document(
                notebook_id=NOTEBOOK_ID,
                user_id=USER_ID,
                file=file,
            )
        )

    assert storage.uploads == []


def test_rag_reader_cannot_run_manager_workflows_or_reach_providers() -> None:
    llm = FakeLlm()
    use_case, storage, _, _ = make_use_case(
        llm,
        access=FakeAccess(can_manage=False),
    )

    with pytest.raises(ForbiddenError):
        run_async(
            use_case.upload_document(
                notebook_id=NOTEBOOK_ID,
                user_id=USER_ID,
                file=upload_file("notas.txt", b"contenido", "text/plain"),
            )
        )
    with pytest.raises(ForbiddenError):
        run_async(
            use_case.generate_flashcards(
                notebook_id=NOTEBOOK_ID,
                user_id=USER_ID,
                request=FlashcardGenerationRequest(count=1),
            )
        )

    assert storage.uploads == []
    assert llm.embedding_calls == []
    assert llm.chat_payloads == []


def test_rag_reserves_durable_ingestion_quota_before_cpu_heavy_parsing() -> None:
    usage = FakeUsage()
    use_case, storage, _, _ = make_use_case(
        usage=usage,
        document_processor=ExplodingDocumentProcessor(),
    )

    with pytest.raises(BadRequestError, match="malformado"):
        run_async(
            use_case.upload_document(
                notebook_id=NOTEBOOK_ID,
                user_id=USER_ID,
                file=upload_file("notas.txt", b"contenido", "text/plain"),
            )
        )

    assert usage.calls == [
        {
            "actor_id": str(USER_ID),
            "operation": "document_embedding",
            "units": 1,
        }
    ]
    assert storage.uploads == []


def test_rag_retries_a_previously_failed_document_hash() -> None:
    use_case, storage, _, _ = make_use_case()
    content = b"contenido reintentable"
    content_hash = use_case.document_processor.content_hash(content)
    use_case.documents.items["00000000-0000-0000-0000-000000000040"] = {
        "document_id": "00000000-0000-0000-0000-000000000040",
        "notebook_id": str(NOTEBOOK_ID),
        "content_hash": content_hash,
        "processing_status": "failed",
        "storage_path": f"{NOTEBOOK_ID}/failed.txt",
    }

    response = run_async(
        use_case.upload_document(
            notebook_id=NOTEBOOK_ID,
            user_id=USER_ID,
            file=upload_file("notas.txt", content, "text/plain"),
        )
    )

    assert response.data.processing_status == "completed"
    assert f"{NOTEBOOK_ID}/failed.txt" in storage.deleted


def test_rag_rejects_unconfigured_chat_model_before_storing_message() -> None:
    use_case, _, _, conversations = make_use_case()

    with pytest.raises(BadRequestError, match="no esta permitido"):
        run_async(
            use_case.chat(
                conversation_id=CONVERSATION_ID,
                user_id=USER_ID,
                request=ChatRequest(
                    content="Que usa la fotosintesis?",
                    model="vendor/modelo-no-permitido",
                ),
            )
        )

    assert conversations.messages == []


def test_rag_generates_and_persists_flashcards_from_notebook_sources() -> None:
    llm = FakeLlm(
        [
            {
                "flashcards": [
                    {"question": "¿Que usa la fotosintesis?", "answer": "Luz."},
                    {"question": "¿Que producen las plantas?", "answer": "Energia quimica."},
                ]
            }
        ]
    )
    use_case, _, _, _ = make_use_case(llm)

    response = run_async(
        use_case.generate_flashcards(
            notebook_id=NOTEBOOK_ID,
            user_id=USER_ID,
            request=FlashcardGenerationRequest(count=2),
        )
    )

    assert len(response.data) == 2
    assert len(use_case.questions.items) == 2
    assert len(use_case.flashcards.items) == 2
    assert all(item["type"] == "open" for item in use_case.questions.items)
    response_format = llm.chat_payloads[0]["response_format"]
    assert response_format["type"] == "json_schema"
    assert response_format["json_schema"]["strict"] is True


def test_rag_lists_flashcards_with_study_answers_after_generation() -> None:
    use_case, _, _, _ = make_use_case(generation=FakeGeneration())

    response = run_async(
        use_case.list_flashcards(
            notebook_id=NOTEBOOK_ID,
            user_id=USER_ID,
            limit=20,
            offset=0,
        )
    )

    assert response.data[0].question == "¿Qué usa la fotosíntesis?"
    assert response.data[0].answer == "Luz."


def test_rag_generates_exam_with_all_question_types_and_persists_relations() -> None:
    llm = FakeLlm(
        [
            {
                "title": "Examen de fotosintesis",
                "description": "Evaluacion basada en las notas.",
                "questions": [
                    {
                        "type": "true_false",
                        "statement": "La fotosintesis usa luz.",
                        "correct_answer": True,
                    },
                    {
                        "type": "multiple_choice",
                        "statement": "¿Que fuente usa la fotosintesis?",
                        "options": ["Luz", "Sonido", "Gravedad"],
                        "correct_option_index": 0,
                    },
                    {
                        "type": "open",
                        "statement": "Explica el papel de la luz.",
                        "expected_answer": "Aporta energia al proceso.",
                    },
                ],
            }
        ]
    )
    use_case, _, _, _ = make_use_case(llm)

    response = run_async(
        use_case.generate_exam(
            notebook_id=NOTEBOOK_ID,
            user_id=USER_ID,
            request=ExamGenerationRequest(
                true_false_count=1,
                multiple_choice_count=1,
                open_count=1,
            ),
        )
    )

    assert response.data.name == "Examen de fotosintesis"
    assert len(response.data.questions) == 3
    assert len(use_case.exams.items) == 1
    assert len(use_case.exam_questions.items) == 3
    assert len(use_case.questions.items) == 3
    assert len(use_case.question_options.items) == 5
    assert sum(item["is_correct"] for item in use_case.question_options.items) == 2
    assert all(not hasattr(item, "expected_answer") for item in response.data.questions)
    assert all(
        not hasattr(option, "is_correct")
        for question in response.data.questions
        for option in question.options
    )
    schema = llm.chat_payloads[0]["response_format"]["json_schema"]["schema"]
    nodes: list[dict[str, Any]] = []

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            nodes.append(value)
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(schema)
    assert all("discriminator" in node for node in nodes if "oneOf" in node)
    object_nodes = [node for node in nodes if node.get("type") == "object"]
    assert object_nodes
    assert all(node.get("additionalProperties") is False for node in object_nodes)
    assert all(
        set(node.get("required", [])).issubset(set(node.get("properties", {})))
        for node in object_nodes
    )
    question_items = schema["properties"]["questions"]["items"]
    assert len(question_items["oneOf"]) == 3
    assert question_items["discriminator"]["propertyName"] == "type"


def test_rag_exam_endpoint_path_uses_atomic_persistence_payload() -> None:
    llm = FakeLlm(
        [
            {
                "title": "Examen de fotosintesis",
                "description": "Evaluacion basada en las notas.",
                "questions": [
                    {
                        "type": "true_false",
                        "statement": "La fotosintesis usa luz.",
                        "correct_answer": True,
                    }
                ],
            }
        ]
    )
    generation = FakeGeneration()
    use_case, _, _, _ = make_use_case(llm, generation=generation)

    response = run_async(
        use_case.generate_exam(
            notebook_id=NOTEBOOK_ID,
            user_id=USER_ID,
            request=ExamGenerationRequest(
                true_false_count=1,
                multiple_choice_count=0,
                open_count=0,
            ),
        )
    )

    assert str(response.data.exam_id) == "30000000-0000-0000-0000-000000000001"
    assert len(response.data.questions) == 1
    assert len(response.data.questions[0].options) == 2
    assert llm.chat_payloads[0]["max_tokens"] == 580
    assert generation.exam_calls == [
        {
            "actor_id": str(USER_ID),
            "notebook_id": str(NOTEBOOK_ID),
            "name": "Examen de fotosintesis",
            "description": "Evaluacion basada en las notas.",
            "questions": [
                {
                    "type": "true_false",
                    "statement": "La fotosintesis usa luz.",
                    "expected_answer": None,
                    "options": [
                        {
                            "option_text": "Verdadero",
                            "is_correct": True,
                            "option_order": 1,
                        },
                        {
                            "option_text": "Falso",
                            "is_correct": False,
                            "option_order": 2,
                        },
                    ],
                }
            ],
        }
    ]
    assert use_case.exams.items == []
    assert use_case.questions.items == []
    assert use_case.exam_questions.items == []
    assert use_case.question_options.items == []


@pytest.mark.parametrize(
    ("true_false_count", "multiple_choice_count", "open_count", "expected"),
    [
        (1, 0, 0, 580),
        (1, 1, 1, 1030),
            (3, 4, 3, 2000),
        (0, 10, 10, 2000),
    ],
)
def test_rag_exam_output_budget_scales_without_requesting_unaffordable_maximum(
    true_false_count: int,
    multiple_choice_count: int,
    open_count: int,
    expected: int,
) -> None:
    request = ExamGenerationRequest(
        true_false_count=true_false_count,
        multiple_choice_count=multiple_choice_count,
        open_count=open_count,
    )

    assert RagStudyMaterialWorkflow._exam_max_tokens(request) == expected


def test_rag_rejects_invalid_structured_output_before_persisting() -> None:
    llm = FakeLlm(["esto no es json"])
    use_case, _, _, _ = make_use_case(llm)

    with pytest.raises(BadRequestError, match="JSON estructurado invalido"):
        run_async(
            use_case.generate_flashcards(
                notebook_id=NOTEBOOK_ID,
                user_id=USER_ID,
                request=FlashcardGenerationRequest(count=2),
            )
        )

    assert use_case.questions.items == []
    assert use_case.flashcards.items == []
