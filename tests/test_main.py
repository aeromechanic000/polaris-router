from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from polaris.models import ChatCompletionResponse, ChatChoice, ChatMessage, Usage


def _mock_response(model="fake-model", content="Hello!"):
    return ChatCompletionResponse(
        id="chatcmpl-test",
        model=model,
        choices=[ChatChoice(index=0, message=ChatMessage(role="assistant", content=content), finish_reason="stop")],
        usage=Usage(prompt_tokens=5, completion_tokens=2, total_tokens=7),
    )


def test_list_models(client):
    resp = client.get("/v1/models")
    assert resp.status_code == 200
    body = resp.json()
    assert body["object"] == "list"
    ids = [m["id"] for m in body["data"]]
    assert "test-model" in ids
    assert "single-ep" in ids


def test_chat_completion_model_not_found(client):
    resp = client.post(
        "/v1/chat/completions",
        json={"model": "nonexistent", "messages": [{"role": "user", "content": "hi"}]},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_chat_completion_success(app):
    mock_resp = _mock_response()
    with patch("polaris.providers.openai.OpenAIProvider.chat_completion", new_callable=AsyncMock, return_value=mock_resp):
        client = TestClient(app)
        resp = client.post(
            "/v1/chat/completions",
            json={"model": "single-ep", "messages": [{"role": "user", "content": "hi"}]},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["choices"][0]["message"]["content"] == "Hello!"
        assert body["model"] == "fake-model"


@pytest.mark.asyncio
async def test_chat_completion_fallback(app):
    mock_resp = _mock_response(content="Fallback response")
    with patch(
        "polaris.providers.openai.OpenAIProvider.chat_completion",
        new_callable=AsyncMock,
        side_effect=[httpx.ConnectError("connection refused"), mock_resp],
    ):
        client = TestClient(app)
        resp = client.post(
            "/v1/chat/completions",
            json={"model": "test-model", "messages": [{"role": "user", "content": "hi"}]},
        )
        assert resp.status_code == 200
        assert resp.json()["choices"][0]["message"]["content"] == "Fallback response"


@pytest.mark.asyncio
async def test_chat_completion_all_fail(app):
    with patch(
        "polaris.providers.openai.OpenAIProvider.chat_completion",
        new_callable=AsyncMock,
        side_effect=httpx.ConnectError("down"),
    ):
        client = TestClient(app)
        resp = client.post(
            "/v1/chat/completions",
            json={"model": "test-model", "messages": [{"role": "user", "content": "hi"}]},
        )
        assert resp.status_code == 502


def test_extra_params_pass_through():
    from polaris.models import ChatCompletionRequest

    req = ChatCompletionRequest(
        model="test",
        messages=[{"role": "user", "content": "hi"}],
        temperature=0.5,
        some_custom_field="custom_value",
    )
    assert req.model_extra["some_custom_field"] == "custom_value"
    assert req.temperature == 0.5
