from __future__ import annotations

import json
import time
import uuid
from collections.abc import AsyncIterator
from typing import Any

import httpx

from polaris.models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    EndpointConfig,
    StreamChunk,
)
from polaris.providers.base import BaseProvider


class OpenAIProvider(BaseProvider):
    def _build_url(self, endpoint: EndpointConfig) -> str:
        base = endpoint.base_url.rstrip("/")
        return f"{base}/chat/completions"

    def _build_headers(self, endpoint: EndpointConfig) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {endpoint.api_key}",
            "Content-Type": "application/json",
        }

    def _build_payload(self, endpoint: EndpointConfig, request: ChatCompletionRequest) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": endpoint.model,
            "messages": [m.model_dump(exclude_none=True) for m in request.messages],
            "stream": request.stream,
        }
        for field in ("temperature", "max_tokens", "top_p", "n", "stop"):
            val = getattr(request, field, None)
            if val is not None:
                payload[field] = val
        # Pass through any extra fields the client sent
        if request.model_extra:
            payload.update(request.model_extra)
        return payload

    async def chat_completion(
        self, endpoint: EndpointConfig, request: ChatCompletionRequest, extra: dict[str, Any] | None = None
    ) -> ChatCompletionResponse:
        url = self._build_url(endpoint)
        headers = self._build_headers(endpoint)
        payload = self._build_payload(endpoint, request)

        async with httpx.AsyncClient(timeout=endpoint.timeout) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            return ChatCompletionResponse.model_validate(resp.json())

    async def chat_completion_stream(
        self, endpoint: EndpointConfig, request: ChatCompletionRequest, extra: dict[str, Any] | None = None
    ) -> AsyncIterator[StreamChunk]:
        url = self._build_url(endpoint)
        headers = self._build_headers(endpoint)
        payload = self._build_payload(endpoint, request)
        chunk_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
        created = int(time.time())

        async with httpx.AsyncClient(timeout=endpoint.timeout) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    line = line.strip()
                    if not line or not line.startswith("data: "):
                        continue
                    data = line[6:]
                    if data == "[DONE]":
                        return
                    try:
                        raw = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    chunk = StreamChunk.model_validate(raw)
                    chunk.id = chunk.id or chunk_id
                    chunk.created = chunk.created or created
                    chunk.model = chunk.model or endpoint.model
                    yield chunk
