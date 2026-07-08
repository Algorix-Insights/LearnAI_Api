from __future__ import annotations

import asyncio
from collections.abc import Callable, Mapping, Sequence
from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Any, Protocol


Message = Mapping[str, Any]
SdkFactory = Callable[..., AbstractContextManager[Any]]


class OpenRouterClientError(Exception):
    pass


class _ChatResource(Protocol):
    def send(self, **kwargs: Any) -> Any:
        raise NotImplementedError


class _EmbeddingsResource(Protocol):
    def generate(self, **kwargs: Any) -> Any:
        raise NotImplementedError

    def list_models(self, **kwargs: Any) -> Any:
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
        messages: Sequence[Message],
        model: str | None = None,
        stream: bool = False,
        **params: Any,
    ) -> Any:
        payload = self._clean_payload(
            {
                "messages": list(messages),
                "model": model,
                "stream": stream,
                **params,
            }
        )
        return await asyncio.to_thread(self._chat_completion, payload)

    async def completions(self, model: str, prompt: str, **params: Any) -> Any:
        return await self.chat_completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            **params,
        )

    async def embeddings(
        self,
        *,
        model: str,
        input: str | Sequence[str],
        **params: Any,
    ) -> Any:
        payload = self._clean_payload({"model": model, "input": input, **params})
        return await asyncio.to_thread(self._embeddings, payload)

    async def embedding_models(self, **params: Any) -> Any:
        payload = self._clean_payload(params)
        return await asyncio.to_thread(self._embedding_models, payload)

    def _chat_completion(self, payload: dict[str, Any]) -> Any:
        with self._open_router() as open_router:
            response = open_router.chat.send(**payload)
            if payload.get("stream"):
                with response as event_stream:
                    return list(event_stream)
            return response

    def _embeddings(self, payload: dict[str, Any]) -> Any:
        with self._open_router() as open_router:
            return open_router.embeddings.generate(**payload)

    def _embedding_models(self, payload: dict[str, Any]) -> Any:
        with self._open_router() as open_router:
            return open_router.embeddings.list_models(**payload)

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

    def _clean_payload(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in payload.items() if value is not None}
