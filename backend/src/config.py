"""
Configuration settings for VoiceSnap backend using Pydantic Settings.
"""
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # API Keys
    elevenlabs_api_key: str = Field(default="", alias="ELEVENLABS_API_KEY")
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    
    # CORS Configuration
    cors_origins: List[str] = Field(
        default=["*"],
        alias="CORS_ORIGINS"
    )
    
    # Application Settings
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=False, alias="DEBUG")
    
    # File Upload Settings
    max_file_size: int = Field(default=10 * 1024 * 1024, alias="MAX_FILE_SIZE")  # 10MB
    allowed_image_types: List[str] = Field(
        default=["image/jpeg", "image/png", "image/webp", "image/avif"],
        alias="ALLOWED_IMAGE_TYPES"
    )
    
    # Session Settings
    session_timeout: int = Field(default=3600, alias="SESSION_TIMEOUT")  # 1 hour
    
    # API Rate Limiting
    api_rate_limit: int = Field(default=100, alias="API_RATE_LIMIT")  # requests per minute
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }


# Global settings instance
settings = Settings()