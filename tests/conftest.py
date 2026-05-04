from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from polaris.main import create_app
from polaris.models import AppConfig, EndpointConfig, ModelConfig


@pytest.fixture
def test_config():
    return AppConfig(
        models={
            "test-model": ModelConfig(
                strategy="round-robin",
                endpoints=[
                    EndpointConfig(
                        base_url="http://fake-upstream.test/v1",
                        model="fake-model",
                        api_key="fake-key",
                    ),
                    EndpointConfig(
                        base_url="http://fake-upstream-2.test/v1",
                        model="fake-model-2",
                        api_key="fake-key-2",
                    ),
                ],
            ),
            "single-ep": ModelConfig(
                strategy="round-robin",
                endpoints=[
                    EndpointConfig(
                        base_url="http://fake-upstream.test/v1",
                        model="fake-model",
                        api_key="fake-key",
                    ),
                ],
            ),
        },
    )


@pytest.fixture
def app(test_config):
    return create_app(test_config)


@pytest.fixture
def client(app):
    return TestClient(app)
