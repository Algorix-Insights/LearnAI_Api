from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable, Mapping, Sequence
from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Any, NoReturn, Protocol, TypeVar, cast

from app.application.interfaces import (
    ChatCompletionPayload,
    EmbeddingInput,
    EmbeddingModelsPayload,
    EmbeddingPayload,
    JsonObject,
    JsonValue,
    OpenRouterChatResponse,
    OpenRouterEmbeddingModelsResponse,
    OpenRouterEmbeddingResponse,
    OpenRouterMessage,
    OpenRouterStreamEvent,
)
from app.core.exceptions import AiServiceUnavailableError

SdkFactory = Callable[..., AbstractContextManager[Any]]
PayloadT = TypeVar("PayloadT", bound=Mapping[str, Any])
logger = logging.getLogger("uvicorn.error.learnia.ai")


class OpenRouterClientError(Exception):
    pass


class _ChatResource(Protocol):
    def send(self, **kwargs: object) -> object:
        raise NotImplementedError


class _EmbeddingsResource(Protocol):
    def generate(self, **kwargs: object) -> object:
        raise NotImplementedError

    def list_models(self, **kwargs: object) -> object:
        raise NotImplementedError


class _OpenRouterSdk(Protocol):
    chat: _ChatResource
    embeddings: _EmbeddingsResource


@dataclass(frozen=True)
class OpenRouterClientConfig:
    api_key: str
    http_referer: str | None = None
    app_title: str | None = None
    app_categories: str | None = None


class OpenRouterClient:
    def __init__(
        self,
        api_key: str,
        *,
        http_referer: str | None = None,
        app_title: str | None = "LearnIA API",
        app_categories: str | None = None,
        sdk_factory: SdkFactory | None = None,
    ) -> None:
        self.config = OpenRouterClientConfig(
            api_key=api_key,
            http_referer=http_referer,
            app_title=app_title,
            app_categories=app_categories,
        )
        self._sdk_factory = sdk_factory

    async def chat_completion(
        self,
        *,
        messages: Sequence[OpenRouterMessage],
        model: str | None = None,
        stream: bool = False,
        **params: JsonValue,
    ) -> OpenRouterChatResponse:
        payload: ChatCompletionPayload = self._clean_payload(
            {
                "messages": list(messages),
                "model": model,
                "stream": stream,
                **params,
            }
        )
        return await asyncio.to_thread(self._chat_completion, payload)

    async def completions(
        self, model: str, prompt: str, **params: JsonValue
    ) -> OpenRouterChatResponse:
        return await self.chat_completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            **params,
        )

    async def embeddings(
        self,
        *,
        model: str,
        input: EmbeddingInput,
        **params: JsonValue,
    ) -> OpenRouterEmbeddingResponse:
        payload: EmbeddingPayload = self._clean_payload({"model": model, "input": input, **params})
        return await asyncio.to_thread(self._embeddings, payload)

    async def embedding_models(self, **params: JsonValue) -> OpenRouterEmbeddingModelsResponse:
        payload: EmbeddingModelsPayload = self._clean_payload(params)
        return await asyncio.to_thread(self._embedding_models, payload)

    def _chat_completion(self, payload: ChatCompletionPayload) -> OpenRouterChatResponse:
        try:
            with self._open_router() as open_router:
                response = open_router.chat.send(**payload)
                if payload.get("stream"):
                    with response as event_stream:
                        return [
                            cast(OpenRouterStreamEvent, self._json_object(event))
                            for event in event_stream
                        ]
                return self._json_object(response)
        except (AiServiceUnavailableError, OpenRouterClientError):
            raise
        except Exception as exc:
            self._raise_service_unavailable(
                operation="chat_completion",
                model=payload.get("model"),
                exc=exc,
            )

    def _embeddings(self, payload: EmbeddingPayload) -> OpenRouterEmbeddingResponse:
        try:
            with self._open_router() as open_router:
                return self._json_object(open_router.embeddings.generate(**payload))
        except (AiServiceUnavailableError, OpenRouterClientError):
            raise
        except Exception as exc:
            self._raise_service_unavailable(
                operation="embeddings",
                model=payload.get("model"),
                exc=exc,
            )

    def _embedding_models(
        self, payload: EmbeddingModelsPayload
    ) -> OpenRouterEmbeddingModelsResponse:
        try:
            with self._open_router() as open_router:
                return self._json_object(open_router.embeddings.list_models(**payload))
        except (AiServiceUnavailableError, OpenRouterClientError):
            raise
        except Exception as exc:
            self._raise_service_unavailable(
                operation="embedding_models",
                model=None,
                exc=exc,
            )

    @staticmethod
    def _raise_service_unavailable(
        *,
        operation: str,
        model: JsonValue | None,
        exc: Exception,
    ) -> NoReturn:
        upstream_status = getattr(exc, "status_code", None)
        if not isinstance(upstream_status, int):
            upstream_status = None
        safe_model = model if isinstance(model, str) else "default"
        logger.warning(
            "openrouter_request_failed operation=%s model=%s upstream_status=%s error_type=%s",
            operation,
            safe_model,
            upstream_status if upstream_status is not None else "unknown",
            type(exc).__name__,
        )
        raise AiServiceUnavailableError() from exc

    def _open_router(self) -> AbstractContextManager[_OpenRouterSdk]:
        if not self.config.api_key:
            raise OpenRouterClientError("OPENROUTER_API_KEY no configurado.")

        factory = self._sdk_factory or self._load_sdk_factory()
        return factory(**self._client_kwargs())

    def _client_kwargs(self) -> dict[str, str]:
        return self._clean_payload(
            {
                "api_key": self.config.api_key,
                "http_referer": self.config.http_referer,
                "x_open_router_title": self.config.app_title,
                "x_open_router_categories": self.config.app_categories,
            }
        )

    def _load_sdk_factory(self) -> SdkFactory:
        try:
            from openrouter import OpenRouter
        except ImportError as exc:
            raise OpenRouterClientError(
                "Dependencia openrouter no instalada. Ejecuta `uv sync`."
            ) from exc
        return OpenRouter

    def _clean_payload(self, payload: Mapping[str, Any]) -> PayloadT:
        cleaned = {key: value for key, value in payload.items() if value is not None}
        return cast(PayloadT, cleaned)

    def _json_object(self, value: object) -> JsonObject:
        converted = self._json_value(value)
        if not isinstance(converted, Mapping):
            raise OpenRouterClientError("OpenRouter devolvio una respuesta no estructurada.")
        return cast(JsonObject, converted)

    def _json_value(self, value: object) -> JsonValue:
        model_dump = getattr(value, "model_dump", None)
        if callable(model_dump):
            return self._json_value(model_dump(mode="json"))
        if isinstance(value, Mapping):
            return {str(key): self._json_value(item) for key, item in value.items()}
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            return [self._json_value(item) for item in value]
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        raise OpenRouterClientError("OpenRouter devolvio un valor no serializable.")
