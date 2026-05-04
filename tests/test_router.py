from __future__ import annotations

from polaris.models import EndpointConfig, ModelConfig
from polaris.router import Router


def _make_endpoints(n: int) -> list[EndpointConfig]:
    return [
        EndpointConfig(
            base_url=f"http://ep-{i}.test/v1",
            model=f"model-{i}",
            api_key=f"key-{i}",
        )
        for i in range(n)
    ]


def test_round_robin_cycles():
    router = Router()
    config = ModelConfig(strategy="round-robin", endpoints=_make_endpoints(3))
    results = [router.select("m", config) for _ in range(6)]
    urls = [ep.base_url for ep in results]
    assert urls == [
        "http://ep-0.test/v1",
        "http://ep-1.test/v1",
        "http://ep-2.test/v1",
        "http://ep-0.test/v1",
        "http://ep-1.test/v1",
        "http://ep-2.test/v1",
    ]


def test_round_robin_different_models_independent():
    router = Router()
    config_a = ModelConfig(strategy="round-robin", endpoints=_make_endpoints(2))
    config_b = ModelConfig(strategy="round-robin", endpoints=_make_endpoints(3))
    a1 = router.select("model-a", config_a)
    a2 = router.select("model-a", config_a)
    b1 = router.select("model-b", config_b)
    assert a1.base_url == "http://ep-0.test/v1"
    assert a2.base_url == "http://ep-1.test/v1"
    assert b1.base_url == "http://ep-0.test/v1"


def test_random_strategy():
    router = Router()
    config = ModelConfig(strategy="random", endpoints=_make_endpoints(10))
    results = {router.select("m", config).base_url for _ in range(50)}
    assert len(results) > 1


def test_failover_always_first():
    router = Router()
    config = ModelConfig(strategy="failover", endpoints=_make_endpoints(3))
    for _ in range(5):
        assert router.select("m", config).base_url == "http://ep-0.test/v1"
