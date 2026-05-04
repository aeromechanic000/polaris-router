from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


# --- Config models ---


class EndpointConfig(BaseModel):
    base_url: str
    model: str
    api_key: str
    provider: Literal["openai", "anthropic"] | None = None
    timeout: float = 60.0


class ModelConfig(BaseModel):
    strategy: Literal["round-robin", "random", "failover"] = "round-robin"
    endpoints: list[EndpointConfig]


class AppConfig(BaseModel):
    models: dict[str, ModelConfig] = {}


# --- OpenAI-compatible request/response models ---


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str | list[Any] | None = None


class ChatCompletionRequest(BaseModel):
    model: str
    messages: list[ChatMessage]
    stream: bool = False
    temperature: float | None = None
    max_tokens: int | None = None
    top_p: float | None = None
    n: int | None = None
    stop: str | list[str] | None = None

    model_config = {"extra": "allow"}


class Usage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatChoice(BaseModel):
    index: int = 0
    message: ChatMessage
    finish_reason: str | None = None


class ChatCompletionResponse(BaseModel):
    id: str = ""
    object: str = "chat.completion"
    created: int = 0
    model: str = ""
    choices: list[ChatChoice]
    usage: Usage = Field(default_factory=Usage)


# --- Streaming models ---


class Delta(BaseModel):
    role: str | None = None
    content: str | None = None


class StreamChoice(BaseModel):
    index: int = 0
    delta: Delta
    finish_reason: str | None = None


class StreamChunk(BaseModel):
    id: str = ""
    object: str = "chat.completion.chunk"
    created: int = 0
    model: str = ""
    choices: list[StreamChoice]
