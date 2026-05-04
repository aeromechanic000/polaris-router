from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any

from polaris.models import (
    AnthropicRequest,
    AnthropicResponse,
    EndpointConfig,
)


class BaseProvider(ABC):
    @abstractmethod
    async def chat_completion(
        self, endpoint: EndpointConfig, request: AnthropicRequest, extra: dict[str, Any] | None = None
    ) -> AnthropicResponse: ...

    @abstractmethod
    async def chat_completion_stream(
        self, endpoint: EndpointConfig, request: AnthropicRequest, extra: dict[str, Any] | None = None
    ) -> AsyncIterator[bytes]: ...
