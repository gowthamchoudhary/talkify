"""
Dependency injection setup for FastAPI services.
"""
from typing import AsyncGenerator
import aiohttp
from fastapi import Depends

from .config import settings


class HTTPClientManager:
    """Manages HTTP client sessions for external API calls."""
    
    def __init__(self):
        self._session: aiohttp.ClientSession | None = None
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP client session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session
    
    async def close(self):
        """Close HTTP client session."""
        if self._session and not self._session.closed:
            await self._session.close()


# Global HTTP client manager
http_client_manager = HTTPClientManager()


async def get_http_session() -> AsyncGenerator[aiohttp.ClientSession, None]:
    """Dependency to provide HTTP client session."""
    session = await http_client_manager.get_session()
    try:
        yield session
    finally:
        # Session cleanup is handled by the manager
        pass


def get_settings():
    """Dependency to provide application settings."""
    return settings


class ServiceDependencies:
    """Container for service dependencies."""
    
    @staticmethod
    def get_elevenlabs_config():
        """Get ElevenLabs API configuration."""
        return {
            "api_key": settings.elevenlabs_api_key,
            "base_url": "https://api.elevenlabs.io/v1"
        }
    
    @staticmethod
    def get_gemini_config():
        """Get Google Gemini API configuration."""
        return {
            "api_key": settings.gemini_api_key
        }


# Dependency functions for FastAPI
async def get_service_deps() -> ServiceDependencies:
    """Provide service dependencies."""
    return ServiceDependencies()


async def get_elevenlabs_config(
    deps: ServiceDependencies = Depends(get_service_deps)
):
    """Dependency for ElevenLabs configuration."""
    return deps.get_elevenlabs_config()


async def get_gemini_config(
    deps: ServiceDependencies = Depends(get_service_deps)
):
    """Dependency for Gemini configuration."""
    return deps.get_gemini_config()