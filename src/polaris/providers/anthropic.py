from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx

from polaris.models import (
    AnthropicRequest,
    AnthropicResponse,
    EndpointConfig,
)
from polaris.providers.base import BaseProvider


class AnthropicProvider(BaseProvider):
    def _build_url(self, endpoint: EndpointConfig) -> str:
        base = endpoint.base_url.rstrip("/")
        return f"{base}/messages"

    def _build_headers(self, endpoint: EndpointConfig) -> dict[str, str]:
        return {
            "x-api-key": endpoint.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

    def _build_payload(self, endpoint: EndpointConfig, request: AnthropicRequest) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": endpoint.model,
            "messages": [m.model_dump(exclude_none=True) for m in request.messages],
            "max_tokens": request.max_tokens,
            "stream": request.stream,
        }
        for field in ("system", "temperature", "top_p", "stop_sequences", "metadata"):
            val = getattr(request, field, None)
            if val is not None:
                payload[field] = val
        if request.model_extra:
            payload.update(request.model_extra)
        return payload

    async def chat_completion(
        self, endpoint: EndpointConfig, request: AnthropicRequest, extra: dict[str, Any] | None = None
    ) -> AnthropicResponse:
        url = self._build_url(endpoint)
        headers = self._build_headers(endpoint)
        payload = self._build_payload(endpoint, request)

        async with httpx.AsyncClient(timeout=endpoint.timeout) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            return AnthropicResponse.model_validate(resp.json())

    async def chat_completion_stream(
        self, endpoint: EndpointConfig, request: AnthropicRequest, extra: dict[str, Any] | None = None
    ) -> AsyncIterator[bytes]:
        url = self._build_url(endpoint)
        headers = self._build_headers(endpoint)
        payload = self._build_payload(endpoint, request)

        async with httpx.AsyncClient(timeout=endpoint.timeout) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line:
                        yield b"\n"
                        continue
                    yield f"{line}\n".encode()
