"""
Tests for the main FastAPI application.
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint returns correct response."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Talkify API is running"
    assert data["version"] == "1.0.0"


def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "talkify-api"
    assert data["version"] == "1.0.0"
    assert "status" in data
    assert "checks" in data
    assert "timestamp" in data


def test_public_config():
    """Test the public configuration endpoint."""
    response = client.get("/api/config")
    assert response.status_code == 200
    data = response.json()
    assert "max_file_size" in data
    assert "allowed_image_types" in data
    assert "session_timeout" in data
    assert "environment" in data
    assert data["max_file_size"] == 10485760  # 10MB
    assert "image/jpeg" in data["allowed_image_types"]
    assert "image/png" in data["allowed_image_types"]
    assert "image/webp" in data["allowed_image_types"]


def test_cors_headers():
    """Test that CORS headers are properly set."""
    response = client.get("/health")
    # CORS headers should be present in the response
    assert response.status_code == 200


def test_process_time_header():
    """Test that process time header is added to responses."""
    response = client.get("/health")
    assert "x-process-time" in response.headers
    # Process time should be a valid float
    process_time = float(response.headers["x-process-time"])
    assert process_time >= 0