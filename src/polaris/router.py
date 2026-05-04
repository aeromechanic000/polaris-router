from __future__ import annotations

import random as _random

from polaris.models import EndpointConfig, ModelConfig


class Router:
    def __init__(self) -> None:
        self._indices: dict[str, int] = {}

    def select_ordered(self, model_name: str, config: ModelConfig) -> list[EndpointConfig]:
        strategy = config.strategy
        endpoints = config.endpoints

        if strategy == "round-robin":
            idx = self._indices.get(model_name, 0)
            self._indices[model_name] = (idx + 1) % len(endpoints)
            return endpoints[idx:] + endpoints[:idx]
        elif strategy == "random":
            ordered = list(endpoints)
            _random.shuffle(ordered)
            return ordered
        elif strategy == "failover":
            return list(endpoints)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
