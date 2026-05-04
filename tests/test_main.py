from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from polaris.models import AnthropicContentBlock, AnthropicResponse, AnthropicUsage


def _mock_response(model="fake-model", text="Hello!"):
    return AnthropicResponse(
        id="msg-test",
        model=model,
        content=[AnthropicContentBlock(type="text", text=text)],
        stop_reason="end_turn",
        usage=AnthropicUsage(input_tokens=5, output_tokens=2),
    )


def test_list_models(client):
    resp = client.get("/v1/models")
    assert resp.status_code == 200
    body = resp.json()
    assert body["object"] == "list"
    ids = [m["id"] for m in body["data"]]
    assert "test-model" in ids
    assert "single-ep" in ids


def test_messages_model_not_found(client):
    resp = client.post(
        "/v1/messages",
        json={"model": "nonexistent", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 1024},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_messages_success(app):
    mock_resp = _mock_response()
    with patch("polaris.providers.anthropic.AnthropicProvider.chat_completion", new_callable=AsyncMock, return_value=mock_resp):
        client = TestClient(app)
        resp = client.post(
            "/v1/messages",
            json={"model": "single-ep", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 1024},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["content"][0]["text"] == "Hello!"
        assert body["model"] == "fake-model"


@pytest.mark.asyncio
async def test_messages_fallback(app):
    mock_resp = _mock_response(text="Fallback response")
    with patch(
        "polaris.providers.anthropic.AnthropicProvider.chat_completion",
        new_callable=AsyncMock,
        side_effect=[httpx.ConnectError("connection refused"), mock_resp],
    ):
        client = TestClient(app)
        resp = client.post(
            "/v1/messages",
            json={"model": "test-model", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 1024},
        )
        assert resp.status_code == 200
        assert resp.json()["content"][0]["text"] == "Fallback response"


@pytest.mark.asyncio
async def test_messages_all_fail(app):
    with patch(
        "polaris.providers.anthropic.AnthropicProvider.chat_completion",
        new_callable=AsyncMock,
        side_effect=httpx.ConnectError("down"),
    ):
        client = TestClient(app)
        resp = client.post(
            "/v1/messages",
            json={"model": "test-model", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 1024},
        )
        assert resp.status_code == 502


def test_extra_params_pass_through():
    from polaris.models import AnthropicRequest

    req = AnthropicRequest(
        model="test",
        messages=[{"role": "user", "content": "hi"}],
        max_tokens=1024,
        temperature=0.5,
        some_custom_field="custom_value",
    )
    assert req.model_extra["some_custom_field"] == "custom_value"
    assert req.temperature == 0.5
