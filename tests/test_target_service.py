# tests/test_target_service.py
"""Unit tests for Target Service endpoints and chaos triggers."""

import pytest
from fastapi.testclient import TestClient
from target_service.app.main import app
from target_service.app.config import system_state

client = TestClient(app)

def setup_function():
    # Reset to healthy state before each test
    system_state["status"] = "HEALTHY"
    system_state["incident_type"] = None
    system_state["leak_buffer"].clear()

def test_health_check_healthy():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert data["incident"] is None
    assert "latency_ms" in data

def test_prometheus_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "service_up 1" in response.text
    assert "http_requests_total" in response.text

def test_chaos_blocking_io_and_fix():
    # Trigger sabotage
    sabotage_res = client.post("/sabotage/blocking-io")
    assert sabotage_res.status_code == 200

    # Verify state via API diagnostics endpoint
    status_res = client.get("/status")
    assert status_res.status_code == 200
    data = status_res.json()
    assert data["status"] == "DEGRADED"
    assert data["incident_type"] == "BLOCKING_IO"

    # Verify direct in-memory state
    assert system_state["status"] == "DEGRADED"
    assert system_state["incident_type"] == "BLOCKING_IO"

    # Reset with /fix
    fix_res = client.post("/fix")
    assert fix_res.status_code == 200

    # Verify recovery via API diagnostics endpoint
    status_res = client.get("/status")
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "HEALTHY"
    assert status_res.json()["incident_type"] is None

    # Verify direct in-memory recovery
    assert system_state["status"] == "HEALTHY"
    assert system_state["incident_type"] is None
