from __future__ import annotations

import itertools
import random as _random
from collections import defaultdict

from polaris.models import EndpointConfig, ModelConfig


class Router:
    def __init__(self) -> None:
        self._cycles: dict[str, itertools.cycle[EndpointConfig]] = {}

    def _get_cycle(self, model_name: str, endpoints: list[EndpointConfig]) -> itertools.cycle[EndpointConfig]:
        if model_name not in self._cycles:
            self._cycles[model_name] = itertools.cycle(endpoints)
        return self._cycles[model_name]

    def select(self, model_name: str, config: ModelConfig) -> EndpointConfig:
        strategy = config.strategy

        if strategy == "round-robin":
            return next(self._get_cycle(model_name, config.endpoints))
        elif strategy == "random":
            return _random.choice(config.endpoints)
        elif strategy == "failover":
            return config.endpoints[0]
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
