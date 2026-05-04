from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from polaris.config import load_config, resolve_api_key


def test_resolve_plain_key():
    assert resolve_api_key("sk-abc123") == "sk-abc123"


def test_resolve_env_key(monkeypatch):
    monkeypatch.setenv("MY_KEY", "secret-value")
    assert resolve_api_key("env:MY_KEY") == "secret-value"


def test_resolve_env_key_missing():
    with pytest.raises(ValueError, match="Environment variable MISSING_KEY is not set"):
        resolve_api_key("env:MISSING_KEY")


def test_load_config(tmp_path, monkeypatch):
    monkeypatch.setenv("KIMI_API_KEY", "kimi-secret")
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({
        "models": {
            "kimi": {
                "strategy": "round-robin",
                "endpoints": [
                    {
                        "base_url": "https://api.moonshot.cn/v1",
                        "model": "moonshot-v1-8k",
                        "api_key": "env:KIMI_API_KEY",
                        "provider": "openai",
                    }
                ],
            }
        },
    }))
    config = load_config(config_file)
    assert config.models["kimi"].endpoints[0].api_key == "kimi-secret"
