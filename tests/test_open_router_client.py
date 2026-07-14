import asyncio
import logging
from contextlib import AbstractContextManager
from typing import Any

import httpx
from openrouter.errors import (
    PaymentRequiredResponseError,
    PaymentRequiredResponseErrorData,
)
import pytest
from pydantic import BaseModel

from app.core.exceptions import AiServiceUnavailableError
from app.infra.clients import OpenRouterClient, OpenRouterClientError


def run_async(coro):
    return asyncio.run(coro)


class FakeOpenRouter(AbstractContextManager["FakeOpenRouter"]):
    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs
        self.chat = FakeChat()
        self.embeddings = FakeEmbeddings()

    def __enter__(self) -> "FakeOpenRouter":
        return self

    def __exit__(self, *args: Any) -> None:
        return None


class FakeChat:
    def __init__(self) -> None:
        self.payload: dict[str, Any] | None = None

    def send(self, **kwargs: Any) -> dict[str, Any]:
        self.payload = kwargs
        if kwargs.get("stream"):
            return FakeEventStream()
        return {"choices": [{"message": {"content": "ok"}}], "payload": kwargs}


class FakeEmbeddings:
    def __init__(self) -> None:
        self.payload: dict[str, Any] | None = None

    def generate(self, **kwargs: Any) -> dict[str, Any]:
        self.payload = kwargs
        return {"data": [{"embedding": [0.1, 0.2]}], "payload": kwargs}

    def list_models(self, **kwargs: Any) -> dict[str, Any]:
        return {"data": [], "payload": kwargs}


class FakeEventStream(AbstractContextManager["FakeEventStream"]):
    def __enter__(self) -> "FakeEventStream":
        return self

    def __exit__(self, *args: Any) -> None:
        return None

    def __iter__(self):
        return iter([{"delta": "a"}, {"delta": "b"}])


class FakeMessageModel(BaseModel):
    content: str


class FakeChoiceModel(BaseModel):
    message: FakeMessageModel


class FakeChatResponseModel(BaseModel):
    choices: list[FakeChoiceModel]


class FakePydanticChat:
    def send(self, **kwargs: Any) -> FakeChatResponseModel:
        return FakeChatResponseModel(
            choices=[FakeChoiceModel(message=FakeMessageModel(content="respuesta"))]
        )


class FakePydanticOpenRouter(FakeOpenRouter):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.chat = FakePydanticChat()


class FakePaymentRequiredChat:
    def send(self, **kwargs: Any) -> None:
        del kwargs
        data = PaymentRequiredResponseErrorData(
            error={
                "code": 402,
                "message": "secret credits; can only afford 2116 tokens",
            }
        )
        response = httpx.Response(
            402,
            request=httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions"),
        )
        raise PaymentRequiredResponseError(data, response)


class FakePaymentRequiredOpenRouter(FakeOpenRouter):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.chat = FakePaymentRequiredChat()


def test_open_router_client_sends_chat_with_sdk() -> None:
    created: list[FakeOpenRouter] = []

    def factory(**kwargs: Any) -> FakeOpenRouter:
        sdk = FakeOpenRouter(**kwargs)
        created.append(sdk)
        return sdk

    client = OpenRouterClient(
        "test-key",
        http_referer="https://learnia.example",
        app_title="LearnIA",
        sdk_factory=factory,
    )

    response = run_async(
        client.chat_completion(
            model="openai/gpt-5.2",
            messages=[{"role": "user", "content": "Hola"}],
            temperature=0.1,
        )
    )

    assert created[0].kwargs == {
        "api_key": "test-key",
        "http_referer": "https://learnia.example",
        "x_open_router_title": "LearnIA",
    }
    assert response["payload"] == {
        "messages": [{"role": "user", "content": "Hola"}],
        "model": "openai/gpt-5.2",
        "stream": False,
        "temperature": 0.1,
    }


def test_open_router_client_keeps_legacy_prompt_completion_method() -> None:
    client = OpenRouterClient("test-key", sdk_factory=FakeOpenRouter)

    response = run_async(client.completions("openai/gpt-5.2", "Resume esto"))

    assert response["payload"]["messages"] == [{"role": "user", "content": "Resume esto"}]
    assert response["payload"]["model"] == "openai/gpt-5.2"


def test_open_router_client_consumes_stream_inside_sdk_context() -> None:
    client = OpenRouterClient("test-key", sdk_factory=FakeOpenRouter)

    response = run_async(
        client.chat_completion(messages=[{"role": "user", "content": "Hola"}], stream=True)
    )

    assert response == [{"delta": "a"}, {"delta": "b"}]


def test_open_router_client_generates_embeddings_with_sdk() -> None:
    client = OpenRouterClient("test-key", sdk_factory=FakeOpenRouter)

    response = run_async(
        client.embeddings(model="openai/text-embedding-3-small", input=["uno", "dos"])
    )

    assert response["payload"] == {
        "model": "openai/text-embedding-3-small",
        "input": ["uno", "dos"],
    }


def test_open_router_client_requires_api_key() -> None:
    client = OpenRouterClient("", sdk_factory=FakeOpenRouter)

    with pytest.raises(OpenRouterClientError, match="OPENROUTER_API_KEY"):
        run_async(client.embedding_models())


def test_open_router_client_serializes_pydantic_sdk_response() -> None:
    client = OpenRouterClient("test-key", sdk_factory=FakePydanticOpenRouter)

    response = run_async(
        client.chat_completion(messages=[{"role": "user", "content": "Hola"}])
    )

    assert response == {"choices": [{"message": {"content": "respuesta"}}]}


def test_open_router_client_maps_payment_required_to_safe_service_error(caplog) -> None:
    client = OpenRouterClient("test-key", sdk_factory=FakePaymentRequiredOpenRouter)

    with caplog.at_level(logging.WARNING, logger="uvicorn.error.learnia.ai"):
        with pytest.raises(AiServiceUnavailableError) as captured:
            run_async(
                client.chat_completion(
                    model="openai/gpt-5.2",
                    messages=[{"role": "user", "content": "Hola"}],
                )
            )

    error = captured.value
    assert error.status_code == 503
    assert error.message == "Servicio de IA no disponible temporalmente."
    assert isinstance(error.__cause__, PaymentRequiredResponseError)
    assert "credits" not in error.message
    assert "2116" not in error.message
    assert "operation=chat_completion" in caplog.text
    assert "model=openai/gpt-5.2" in caplog.text
    assert "upstream_status=402" in caplog.text
    assert "error_type=PaymentRequiredResponseError" in caplog.text
    assert "secret credits" not in caplog.text
    assert "2116" not in caplog.text
