"""Basic tests for worker service."""
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_endpoint():
    """Test health check returns 200."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "worker"


def test_metrics_endpoint():
    """Test metrics endpoint returns worker stats."""
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "processed_jobs" in data
    assert data["service"] == "worker"
