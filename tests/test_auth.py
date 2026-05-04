from __future__ import annotations


def test_health_no_auth_required(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_models_no_auth_required(client):
    resp = client.get("/v1/models")
    assert resp.status_code == 200
