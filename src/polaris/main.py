from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse

from polaris.config import load_config
from polaris.models import AppConfig, ChatCompletionRequest, ModelConfig
from polaris.providers.openai import OpenAIProvider
from polaris.router import Router

logger = logging.getLogger("polaris")

PROVIDERS = {
    "openai": OpenAIProvider(),
}
DEFAULT_PROVIDER = "openai"


def _get_provider(provider_name: str | None):
    name = provider_name or DEFAULT_PROVIDER
    provider = PROVIDERS.get(name)
    if provider is None:
        raise ValueError(f"Unknown provider: {name}")
    return provider


def create_app(config: AppConfig) -> FastAPI:
    app = FastAPI(title="Polaris")
    app.state.config = config
    app.state.router = Router()
    app.include_router(_health_router)
    app.include_router(_api_router)
    return app


def load_app() -> FastAPI:
    config = load_config()
    return create_app(config)


_health_router = APIRouter()
_api_router = APIRouter()


@_health_router.get("/health")
async def health():
    return {"status": "ok"}


@_api_router.get("/v1/models")
async def list_models(
    request: Request,
):
    config: AppConfig = request.app.state.config
    return {
        "object": "list",
        "data": [
            {"id": name, "object": "model", "owned_by": "polaris"}
            for name in config.models
        ],
    }


@_api_router.post("/v1/chat/completions")
async def chat_completions(
    request: Request,
    body: ChatCompletionRequest,
):
    config: AppConfig = request.app.state.config
    router: Router = request.app.state.router

    model_config = config.models.get(body.model)
    if model_config is None:
        raise HTTPException(status_code=404, detail=f"Model '{body.model}' not found")

    if body.stream:
        return StreamingResponse(
            _stream_with_fallback(body, model_config, router),
            media_type="text/event-stream",
        )

    return await _completion_with_fallback(body, model_config, router)


async def _completion_with_fallback(
    request: ChatCompletionRequest, model_config: ModelConfig, router: Router
):
    errors: list[str] = []
    for endpoint in model_config.endpoints:
        try:
            provider = _get_provider(endpoint.provider)
            return await provider.chat_completion(endpoint, request)
        except Exception as e:
            logger.warning("Endpoint %s failed: %s", endpoint.base_url, e)
            errors.append(f"{endpoint.base_url}: {e}")
    raise HTTPException(status_code=502, detail={"message": "All endpoints failed", "errors": errors})


async def _stream_with_fallback(
    request: ChatCompletionRequest, model_config: ModelConfig, router: Router
) -> AsyncIterator[bytes]:
    for endpoint in model_config.endpoints:
        try:
            provider = _get_provider(endpoint.provider)
            async for chunk in provider.chat_completion_stream(endpoint, request):
                data = f"data: {chunk.model_dump_json()}\n\n"
                yield data.encode()
            yield b"data: [DONE]\n\n"
            return
        except Exception as e:
            logger.warning("Stream endpoint %s failed: %s", endpoint.base_url, e)
            continue
    error_payload = json.dumps({"error": {"message": "All endpoints failed"}})
    yield f"data: {error_payload}\n\n".encode()
    yield b"data: [DONE]\n\n"


app = load_app()
