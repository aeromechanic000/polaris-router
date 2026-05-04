from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel


# --- Config models ---


class EndpointConfig(BaseModel):
    base_url: str
    model: str
    api_key: str
    timeout: float = 60.0


class ModelConfig(BaseModel):
    strategy: Literal["round-robin", "random", "failover"] = "round-robin"
    endpoints: list[EndpointConfig]


class AppConfig(BaseModel):
    models: dict[str, ModelConfig] = {}


# --- Anthropic Messages API models ---


class AnthropicMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str | list[dict[str, Any]]


class AnthropicRequest(BaseModel):
    model: str
    messages: list[AnthropicMessage]
    max_tokens: int
    system: str | list[dict[str, Any]] | None = None
    stream: bool = False
    temperature: float | None = None
    top_p: float | None = None
    stop_sequences: list[str] | None = None
    metadata: dict[str, Any] | None = None

    model_config = {"extra": "allow"}


class AnthropicUsage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0


class AnthropicContentBlock(BaseModel):
    type: str = "text"
    text: str = ""


class AnthropicResponse(BaseModel):
    id: str = ""
    type: Literal["message"] = "message"
    role: Literal["assistant"] = "assistant"
    content: list[AnthropicContentBlock]
    model: str = ""
    stop_reason: str | None = None
    stop_sequence: str | None = None
    usage: AnthropicUsage
