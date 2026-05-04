from __future__ import annotations

import json
import os
from pathlib import Path

from polaris.models import AppConfig


def resolve_api_key(key: str) -> str:
    if key.startswith("env:"):
        var_name = key[4:]
        value = os.environ.get(var_name)
        if value is None:
            raise ValueError(f"Environment variable {var_name} is not set")
        return value
    return key


def load_config(path: str | Path = "config.json") -> AppConfig:
    raw = json.loads(Path(path).read_text())
    config = AppConfig.model_validate(raw)

    # Resolve env: references in api_keys at load time
    for model_config in config.models.values():
        for ep in model_config.endpoints:
            ep.api_key = resolve_api_key(ep.api_key)

    return config
