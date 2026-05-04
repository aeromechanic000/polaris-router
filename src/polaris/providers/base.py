from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any

from polaris.models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    EndpointConfig,
    StreamChunk,
)


class BaseProvider(ABC):
    @abstractmethod
    async def chat_completion(
        self, endpoint: EndpointConfig, request: ChatCompletionRequest, extra: dict[str, Any] | None = None
    ) -> ChatCompletionResponse: ...

    @abstractmethod
    async def chat_completion_stream(
        self, endpoint: EndpointConfig, request: ChatCompletionRequest, extra: dict[str, Any] | None = None
    ) -> AsyncIterator[StreamChunk]: ...
