from fastapi.testclient import TestClient
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app)


def test_home_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Automation Platform Running"
    assert data["status"] == "success"


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "hostname" in data


def test_run_test_endpoint():
    response = client.get("/run-test")
    assert response.status_code == 200
    data = response.json()
    assert data["test_name"] == "sample_ui_test"
    assert data["result"] == "PASSED"