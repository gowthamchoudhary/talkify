"""
Tests for configuration settings.
"""
import pytest
from src.config import Settings


def test_settings_defaults():
    """Test that settings have correct default values."""
    settings = Settings()
    
    # Check default values
    assert settings.environment == "development"
    assert settings.debug is False
    assert settings.max_file_size == 10 * 1024 * 1024  # 10MB
    assert settings.session_timeout == 3600  # 1 hour
    assert settings.api_rate_limit == 100
    
    # Check default CORS origins
    assert "http://localhost:3000" in settings.cors_origins
    assert "http://localhost:5173" in settings.cors_origins
    
    # Check default allowed image types
    assert "image/jpeg" in settings.allowed_image_types
    assert "image/png" in settings.allowed_image_types
    assert "image/webp" in settings.allowed_image_types


def test_settings_with_env_vars(monkeypatch):
    """Test settings with environment variables."""
    # Set environment variables
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test_elevenlabs_key")
    monkeypatch.setenv("GEMINI_API_KEY", "test_gemini_key")
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("MAX_FILE_SIZE", "5242880")  # 5MB
    
    settings = Settings()
    
    assert settings.elevenlabs_api_key == "test_elevenlabs_key"
    assert settings.gemini_api_key == "test_gemini_key"
    assert settings.environment == "production"
    assert settings.debug is True
    assert settings.max_file_size == 5242880