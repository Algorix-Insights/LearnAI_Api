import asyncio
import logging
from typing import Any

import pytest
from pydantic import BaseModel

from app.core.exceptions import AiServiceUnavailableError
from app.infra.clients import GeminiClient, GeminiClientError


def run_async(coro):
    return asyncio.run(coro)


class FakePart:
    def __init__(self, text: str) -> None:
        self.text = text

    @classmethod
    def from_text(cls, text: str) -> "FakePart":
        return cls(text)


class FakeContent:
    def __init__(self, role: str, parts: list[FakePart]) -> None:
        self.role = role
        self.parts = parts


class FakeGenerateContentConfig:
    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs


class FakeTypesModule:
    Content = FakeContent
    Part = FakePart
    GenerateContentConfig = FakeGenerateContentConfig


class FakeModelsResource:
    def __init__(self) -> None:
        self.last_generate_kwargs: dict[str, Any] | None = None
        self.last_embed_kwargs: dict[str, Any] | None = None
        self.should_fail_status: int | None = None

    def generate_content(self, **kwargs: Any) -> Any:
        self.last_generate_kwargs = kwargs
        if self.should_fail_status is not None:
            exc = RuntimeError("API error")
            exc.status_code = self.should_fail_status  # type: ignore[attr-defined]
            raise exc
        return FakeGenerateResponse("respuesta de gemini")

    def embed_content(self, **kwargs: Any) -> Any:
        self.last_embed_kwargs = kwargs
        return FakeEmbedResponse([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])


class FakeGenerateResponse:
    def __init__(self, text: str) -> None:
        self.text = text


class FakeEmbeddingItem:
    def __init__(self, values: list[float]) -> None:
        self.values = values


class FakeEmbedResponse:
    def __init__(self, embeddings: list[list[float]]) -> None:
        self.embeddings = [FakeEmbeddingItem(v) for v in embeddings]


class FakeGenaiClient:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self.models = FakeModelsResource()
        self._types_module = FakeTypesModule


def test_gemini_client_chat_completion_sends_mapped_messages() -> None:
    created: list[FakeGenaiClient] = []

    def factory(api_key: str) -> FakeGenaiClient:
        client = FakeGenaiClient(api_key)
        created.append(client)
        return client

    client = GeminiClient("test-gemini-key", sdk_factory=factory)
    response = run_async(
        client.chat_completion(
            model="gemini-2.5-flash",
            messages=[
                {"role": "system", "content": "Eres un tutor inteligente."},
                {"role": "user", "content": "Hola Gemini"},
            ],
            temperature=0.2,
            max_tokens=1000,
        )
    )

    assert len(created) == 1
    assert created[0].api_key == "test-gemini-key"
    assert response == {"choices": [{"message": {"role": "assistant", "content": "respuesta de gemini"}}]}

    last_kwargs = created[0].models.last_generate_kwargs
    assert last_kwargs is not None
    assert last_kwargs["model"] == "gemini-2.5-flash"
    assert len(last_kwargs["contents"]) == 1
    assert last_kwargs["contents"][0].role == "user"
    assert last_kwargs["contents"][0].parts[0].text == "Hola Gemini"
    
    config = last_kwargs["config"]
    assert config.kwargs["system_instruction"] == "Eres un tutor inteligente."
    assert config.kwargs["temperature"] == 0.2
    assert config.kwargs["max_output_tokens"] == 1000


def test_gemini_client_supports_json_schema_response_format() -> None:
    fake_client = FakeGenaiClient("test-key")
    client = GeminiClient("test-key", sdk_factory=lambda **kwargs: fake_client)
    schema_payload = {
        "type": "object",
        "properties": {"question": {"type": "string"}},
    }

    response = run_async(
        client.chat_completion(
            messages=[{"role": "user", "content": "Genera pregunta"}],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "exam_question",
                    "strict": True,
                    "schema": schema_payload,
                },
            },
        )
    )

    assert response["choices"][0]["message"]["content"] == "respuesta de gemini"
    config = fake_client.models.last_generate_kwargs["config"]
    assert config.kwargs["response_mime_type"] == "application/json"
    assert config.kwargs["response_schema"] == schema_payload


def test_gemini_client_completions() -> None:
    client = GeminiClient("test-key", sdk_factory=FakeGenaiClient)
    response = run_async(client.completions("gemini-1.5-pro", "Completar texto"))
    assert response["choices"][0]["message"]["content"] == "respuesta de gemini"


def test_gemini_client_embeddings() -> None:
    client = GeminiClient("test-key", sdk_factory=FakeGenaiClient)
    response = run_async(
        client.embeddings(model="text-embedding-004", input=["uno", "dos"])
    )
    assert response == {
        "data": [
            {"embedding": [0.1, 0.2, 0.3]},
            {"embedding": [0.4, 0.5, 0.6]},
        ]
    }


def test_gemini_client_embedding_models() -> None:
    client = GeminiClient("test-key", sdk_factory=FakeGenaiClient)
    response = run_async(client.embedding_models())
    assert response == {"data": []}


def test_gemini_client_requires_api_key() -> None:
    client = GeminiClient("", sdk_factory=FakeGenaiClient)
    with pytest.raises(GeminiClientError, match="GEMINI_API_KEY"):
        run_async(client.chat_completion(messages=[{"role": "user", "content": "Hola"}]))


def test_gemini_client_raises_safe_service_error_on_api_failure(caplog) -> None:
    def failing_factory(api_key: str) -> FakeGenaiClient:
        client = FakeGenaiClient(api_key)
        client.models.should_fail_status = 503
        return client

    client = GeminiClient("test-key", sdk_factory=failing_factory)
    with caplog.at_level(logging.WARNING, logger="uvicorn.error.learnia.ai"):
        with pytest.raises(AiServiceUnavailableError) as captured:
            run_async(client.chat_completion(messages=[{"role": "user", "content": "fallo"}]))

    error = captured.value
    assert error.status_code == 503
    assert error.message == "Servicio de IA no disponible temporalmente."
    assert "gemini_request_failed" in caplog.text
    assert "upstream_status=503" in caplog.text
