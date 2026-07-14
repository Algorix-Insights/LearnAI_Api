from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Literal, Protocol, Required, TypeAlias, TypedDict


MessageRole = Literal["system", "user", "assistant", "tool"]
EmbeddingInput = str | Sequence[str]
JsonPrimitive: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonPrimitive | Sequence["JsonValue"] | Mapping[str, "JsonValue"]
JsonObject: TypeAlias = Mapping[str, JsonValue]
OpenRouterStreamEvent: TypeAlias = JsonObject
OpenRouterChatResponse: TypeAlias = JsonObject | list[OpenRouterStreamEvent]
OpenRouterEmbeddingResponse: TypeAlias = JsonObject
OpenRouterEmbeddingModelsResponse: TypeAlias = JsonObject


class OpenRouterMessage(TypedDict, total=False):
    role: Required[MessageRole]
    content: Required[str | Sequence[JsonObject]]
    name: str
    tool_call_id: str
    tool_calls: Sequence[JsonObject]


class ChatCompletionPayload(TypedDict, total=False):
    messages: Required[list[OpenRouterMessage]]
    model: str
    stream: bool
    temperature: float
    top_p: float
    top_k: int
    max_tokens: int
    stop: str | Sequence[str]
    tools: Sequence[JsonObject]
    tool_choice: str | JsonObject
    response_format: JsonObject
    provider: JsonObject
    models: Sequence[str]
    route: str
    transforms: Sequence[str]
    reasoning: JsonObject


class EmbeddingPayload(TypedDict, total=False):
    model: Required[str]
    input: Required[EmbeddingInput]
    encoding_format: Literal["float", "base64"]
    dimensions: int


class EmbeddingModelsPayload(TypedDict, total=False):
    pass


class AiGateway(Protocol):
    async def chat_completion(
        self,
        *,
        messages: Sequence[OpenRouterMessage],
        model: str | None = None,
        stream: bool = False,
        **params: JsonValue,
    ) -> OpenRouterChatResponse:
        raise NotImplementedError

    async def completions(
        self, model: str, prompt: str, **params: JsonValue
    ) -> OpenRouterChatResponse:
        raise NotImplementedError

    async def embeddings(
        self,
        *,
        model: str,
        input: EmbeddingInput,
        **params: JsonValue,
    ) -> OpenRouterEmbeddingResponse:
        raise NotImplementedError

    async def embedding_models(self, **params: JsonValue) -> OpenRouterEmbeddingModelsResponse:
        raise NotImplementedError


OpenRouterGateway: TypeAlias = AiGateway
