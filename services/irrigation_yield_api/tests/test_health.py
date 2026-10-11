"""Tests for service health and root status endpoints."""

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_root_endpoint():
    """Verify root endpoint returns API information and documentation link."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "KisanCare Dual Inference Service"
    assert data["docs"] == "/docs"
    assert len(data["endpoints"]) >= 3


def test_health_endpoint():
    """Verify /health returns status 200 and indicates models are loaded."""
    with TestClient(app) as test_client:
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "kisancare-inference-api"
        assert "version" in data
        assert "timestamp" in data

        models = data["models"]
        assert "irrigation" in models
        assert "yield" in models

        assert models["irrigation"]["loaded"] is True
        assert models["irrigation"]["status"] == "ready"

        assert models["yield"]["loaded"] is True
        assert models["yield"]["status"] == "ready"
