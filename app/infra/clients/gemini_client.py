from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable, Mapping, Sequence
from typing import Any, NoReturn, cast
from app.application.interfaces.ai_gateway import (
    EmbeddingInput,
    JsonObject,
    JsonValue,
    OpenRouterChatResponse,
    OpenRouterEmbeddingModelsResponse,
    OpenRouterEmbeddingResponse,
    OpenRouterMessage,
)
from app.core.exceptions import AiServiceUnavailableError
from google import genai
from google.genai import types

logger = logging.getLogger("uvicorn.error.learnia.ai")
SdkFactory = Callable[..., Any]


class GeminiClientError(Exception):
    pass


class GeminiClient:
    def __init__(
        self,
        api_key: str,
        *,
        sdk_factory: SdkFactory | None = None,
    ) -> None:
        self.api_key = api_key
        self._sdk_factory = sdk_factory

    async def chat_completion(
        self,
        *,
        messages: Sequence[OpenRouterMessage],
        model: str | None = None,
        stream: bool = False,
        **params: JsonValue,
    ) -> OpenRouterChatResponse:
        if stream:
            raise GeminiClientError("Streaming no soportado para GeminiClient actualmente.")
        return await asyncio.to_thread(
            self._chat_completion,
            list(messages),
            model or "gemini-2.5-flash",
            params,
        )

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
        texts = [input] if isinstance(input, str) else list(input)
        return await asyncio.to_thread(self._embeddings, model, texts, params)

    async def embedding_models(self, **params: JsonValue) -> OpenRouterEmbeddingModelsResponse:
        return {"data": []}

    def _chat_completion(
        self,
        messages: list[OpenRouterMessage],
        model: str,
        params: Mapping[str, JsonValue],
    ) -> OpenRouterChatResponse:
        try:
            client, types = self._get_client_and_types()
            contents, system_instructions = self._map_messages(messages, types)

            config_kwargs: dict[str, Any] = {}
            if system_instructions:
                config_kwargs["system_instruction"] = "\n\n".join(system_instructions)

            if "temperature" in params and params["temperature"] is not None:
                try:
                    config_kwargs["temperature"] = float(cast(Any, params["temperature"]))
                except (TypeError, ValueError):
                    pass

            if "max_tokens" in params and params["max_tokens"] is not None:
                try:
                    config_kwargs["max_output_tokens"] = int(cast(Any, params["max_tokens"]))
                except (TypeError, ValueError):
                    pass

            if response_format := params.get("response_format"):
                if isinstance(response_format, Mapping):
                    fmt_type = response_format.get("type")
                    if fmt_type == "json_schema":
                        config_kwargs["response_mime_type"] = "application/json"
                        json_schema_meta = response_format.get("json_schema")
                        if isinstance(json_schema_meta, Mapping) and "schema" in json_schema_meta:
                            config_kwargs["response_schema"] = json_schema_meta["schema"]
                    elif fmt_type in {"json_object", "json"}:
                        config_kwargs["response_mime_type"] = "application/json"

            config = types.GenerateContentConfig(**config_kwargs) if types else config_kwargs
            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )

            text_content = getattr(response, "text", None)
            if text_content is None and isinstance(response, Mapping):
                text_content = response.get("text")
            if not isinstance(text_content, str):
                text_content = ""

            return {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": text_content,
                        }
                    }
                ]
            }
        except (AiServiceUnavailableError, GeminiClientError):
            raise
        except Exception as exc:
            self._raise_service_unavailable(
                operation="chat_completion",
                model=model,
                exc=exc,
            )

    def _embeddings(
        self,
        model: str,
        texts: list[str],
        params: Mapping[str, JsonValue],
    ) -> OpenRouterEmbeddingResponse:
        try:
            client, _ = self._get_client_and_types()
            response = client.models.embed_content(
                model=model,
                contents=texts,
            )

            embeddings_list = getattr(response, "embeddings", None)
            if embeddings_list is None and isinstance(response, Mapping):
                embeddings_list = response.get("embeddings")

            data: list[JsonObject] = []
            if isinstance(embeddings_list, Sequence):
                for item in embeddings_list:
                    values = getattr(item, "values", None)
                    if values is None and isinstance(item, Mapping):
                        values = item.get("values")
                    if isinstance(values, Sequence):
                        data.append({"embedding": [float(x) for x in values]})

            return {"data": data}
        except (AiServiceUnavailableError, GeminiClientError):
            raise
        except Exception as exc:
            self._raise_service_unavailable(
                operation="embeddings",
                model=model,
                exc=exc,
            )

    def _map_messages(
        self,
        messages: list[OpenRouterMessage],
        types: Any,
    ) -> tuple[list[Any], list[str]]:
        contents: list[Any] = []
        system_instructions: list[str] = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if isinstance(content, Sequence) and not isinstance(content, str):
                parts_text = []
                for part in content:
                    if isinstance(part, Mapping) and "text" in part:
                        parts_text.append(str(part["text"]))
                content_str = "\n".join(parts_text)
            else:
                content_str = str(content)

            if role == "system":
                system_instructions.append(content_str)
            else:
                gemini_role = "model" if role == "assistant" else "user"
                if types and hasattr(types, "Content") and hasattr(types, "Part"):
                    contents.append(
                        types.Content(
                            role=gemini_role,
                            parts=[types.Part.from_text(text=content_str)],
                        )
                    )
                else:
                    contents.append(
                        {
                            "role": gemini_role,
                            "parts": [{"text": content_str}],
                        }
                    )

        return contents, system_instructions

    def _get_client_and_types(self) -> tuple[Any, Any]:
        if not self.api_key:
            raise GeminiClientError("GEMINI_API_KEY no configurada.")

        if self._sdk_factory:
            # En tests o inyección personalizada
            client = self._sdk_factory(api_key=self.api_key)
            types_module = getattr(client, "_types_module", None)
            return client, types_module

        return genai.Client(api_key=self.api_key), types

    @staticmethod
    def _raise_service_unavailable(
        *,
        operation: str,
        model: str | None,
        exc: Exception,
    ) -> NoReturn:
        upstream_status = getattr(exc, "status_code", None)
        if not isinstance(upstream_status, int):
            upstream_status = getattr(exc, "code", None)
        if not isinstance(upstream_status, int):
            upstream_status = None

        logger.warning(
            "gemini_request_failed operation=%s model=%s upstream_status=%s error_type=%s",
            operation,
            model or "default",
            upstream_status if upstream_status is not None else "unknown",
            type(exc).__name__,
        )
        raise AiServiceUnavailableError() from exc
