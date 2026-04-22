"""
ElevenLabs API client base class with authentication, rate limiting, and error handling.

This module provides a robust HTTP client for all ElevenLabs API interactions,
implementing proper authentication headers, rate limiting with exponential backoff,
and comprehensive error handling for all API responses.

Requirements: 11.6, 11.7
"""
import asyncio
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import aiohttp
import logging
from urllib.parse import urljoin

from .config import settings
from .exceptions import ElevenLabsError


logger = logging.getLogger(__name__)


@dataclass
class RateLimitInfo:
    """Rate limiting information from API headers."""
    requests_remaining: int
    requests_reset_time: int
    characters_remaining: int
    characters_reset_time: int


class ElevenLabsClient:
    """
    Authenticated HTTP client for ElevenLabs API with rate limiting and retry logic.
    
    This client handles:
    - Proper authentication headers for all requests
    - Rate limiting with exponential backoff
    - Comprehensive error handling and response validation
    - Automatic retries for transient failures
    - Connection pooling and session management
    """
    
    BASE_URL = "https://api.elevenlabs.io/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize ElevenLabs client with API key and default settings.
        
        Args:
            api_key: ElevenLabs API key. If None, uses settings.elevenlabs_api_key
        """
        self.api_key = api_key or settings.elevenlabs_api_key
        if not self.api_key:
            raise ValueError("ElevenLabs API key is required")
        
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limit_info: Optional[RateLimitInfo] = None
        
        # Rate limiting configuration
        self.max_retries = 3
        self.base_delay = 1.0  # Base delay for exponential backoff
        self.max_delay = 60.0  # Maximum delay between retries
        
        # Request timeout configuration
        self.timeout = aiohttp.ClientTimeout(total=30, connect=10)
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with session cleanup."""
        await self.close()
    
    async def _ensure_session(self):
        """Ensure aiohttp session is created and configured."""
        if self.session is None or self.session.closed:
            connector = aiohttp.TCPConnector(
                limit=100,  # Connection pool limit
                limit_per_host=30,  # Per-host connection limit
                ttl_dns_cache=300,  # DNS cache TTL
                use_dns_cache=True,
            )
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=self.timeout,
                headers=self._get_default_headers()
            )
    
    def _get_default_headers(self) -> Dict[str, str]:
        """
        Get default headers for all ElevenLabs API requests.
        
        Returns:
            Dictionary of default headers including authentication
        """
        return {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Talkify/1.0.0"
        }
    
    def _update_rate_limit_info(self, headers: Dict[str, str]):
        """
        Update rate limit information from response headers.
        
        Args:
            headers: Response headers from ElevenLabs API
        """
        try:
            self.rate_limit_info = RateLimitInfo(
                requests_remaining=int(headers.get("x-ratelimit-remaining-requests", 0)),
                requests_reset_time=int(headers.get("x-ratelimit-reset-requests", 0)),
                characters_remaining=int(headers.get("x-ratelimit-remaining-characters", 0)),
                characters_reset_time=int(headers.get("x-ratelimit-reset-characters", 0))
            )
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse rate limit headers: {e}")
    
    async def _wait_for_rate_limit(self):
        """
        Wait if rate limit is exceeded based on current rate limit info.
        """
        if not self.rate_limit_info:
            return
        
        current_time = int(time.time())
        
        # Check if we need to wait for request rate limit
        if self.rate_limit_info.requests_remaining <= 0:
            wait_time = max(0, self.rate_limit_info.requests_reset_time - current_time)
            if wait_time > 0:
                logger.info(f"Rate limit exceeded, waiting {wait_time} seconds")
                await asyncio.sleep(wait_time)
        
        # Check if we need to wait for character rate limit
        if self.rate_limit_info.characters_remaining <= 0:
            wait_time = max(0, self.rate_limit_info.characters_reset_time - current_time)
            if wait_time > 0:
                logger.info(f"Character limit exceeded, waiting {wait_time} seconds")
                await asyncio.sleep(wait_time)
    
    async def _handle_error_response(self, response: aiohttp.ClientResponse) -> None:
        """
        Handle error responses from ElevenLabs API.
        
        Args:
            response: aiohttp response object
            
        Raises:
            ElevenLabsError: With appropriate error message and status code
        """
        try:
            error_data = await response.json()
            error_message = error_data.get("detail", {})
            
            if isinstance(error_message, dict):
                message = error_message.get("message", "Unknown API error")
            elif isinstance(error_message, str):
                message = error_message
            else:
                message = f"HTTP {response.status} error"
                
        except Exception:
            message = f"HTTP {response.status} error - unable to parse response"
        
        # Map common HTTP status codes to user-friendly messages
        status_messages = {
            400: "Invalid request parameters",
            401: "Invalid or missing API key",
            403: "Access forbidden - check API key permissions",
            404: "Requested resource not found",
            422: "Request validation failed",
            429: "Rate limit exceeded",
            500: "ElevenLabs server error",
            502: "ElevenLabs service temporarily unavailable",
            503: "ElevenLabs service unavailable"
        }
        
        if response.status in status_messages:
            message = f"{status_messages[response.status]}: {message}"
        
        raise ElevenLabsError(message, response.status)
    
    async def _make_request_with_retry(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> aiohttp.ClientResponse:
        """
        Make HTTP request with exponential backoff retry logic.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            **kwargs: Additional arguments for aiohttp request
            
        Returns:
            aiohttp.ClientResponse object
            
        Raises:
            ElevenLabsError: If all retry attempts fail
        """
        await self._ensure_session()
        url = urljoin(self.BASE_URL, endpoint.lstrip('/'))
        
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                # Wait for rate limit if needed
                await self._wait_for_rate_limit()
                
                # Make the request
                async with self.session.request(method, url, **kwargs) as response:
                    # Update rate limit info from headers
                    self._update_rate_limit_info(dict(response.headers))
                    
                    # Handle rate limiting with exponential backoff
                    if response.status == 429:
                        if attempt < self.max_retries:
                            delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                            logger.warning(f"Rate limited, retrying in {delay} seconds (attempt {attempt + 1})")
                            await asyncio.sleep(delay)
                            continue
                        else:
                            await self._handle_error_response(response)
                    
                    # Handle server errors with retry
                    elif response.status >= 500:
                        if attempt < self.max_retries:
                            delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                            logger.warning(f"Server error {response.status}, retrying in {delay} seconds (attempt {attempt + 1})")
                            await asyncio.sleep(delay)
                            continue
                        else:
                            await self._handle_error_response(response)
                    
                    # Handle client errors (no retry)
                    elif response.status >= 400:
                        await self._handle_error_response(response)
                    
                    # Success - return response
                    return response
                    
            except aiohttp.ClientError as e:
                last_exception = e
                if attempt < self.max_retries:
                    delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                    logger.warning(f"Network error, retrying in {delay} seconds (attempt {attempt + 1}): {e}")
                    await asyncio.sleep(delay)
                    continue
                else:
                    break
        
        # All retries failed
        error_msg = f"Request failed after {self.max_retries + 1} attempts"
        if last_exception:
            error_msg += f": {last_exception}"
        raise ElevenLabsError(error_msg)
    
    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make GET request to ElevenLabs API.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            
        Returns:
            JSON response data
        """
        response = await self._make_request_with_retry("GET", endpoint, params=params)
        return await response.json()
    
    async def post(
        self, 
        endpoint: str, 
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make POST request to ElevenLabs API.
        
        Args:
            endpoint: API endpoint path
            json_data: JSON data to send
            data: Raw data to send (for file uploads)
            headers: Additional headers
            
        Returns:
            JSON response data
        """
        kwargs = {}
        if json_data is not None:
            kwargs["json"] = json_data
        if data is not None:
            kwargs["data"] = data
        if headers:
            kwargs["headers"] = headers
            
        response = await self._make_request_with_retry("POST", endpoint, **kwargs)
        return await response.json()
    
    async def post_audio(
        self, 
        endpoint: str, 
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> bytes:
        """
        Make POST request expecting audio response.
        
        Args:
            endpoint: API endpoint path
            json_data: JSON data to send
            data: Raw data to send
            headers: Additional headers
            
        Returns:
            Audio data as bytes
        """
        kwargs = {}
        if json_data is not None:
            kwargs["json"] = json_data
        if data is not None:
            kwargs["data"] = data
        if headers:
            kwargs["headers"] = headers
            
        response = await self._make_request_with_retry("POST", endpoint, **kwargs)
        return await response.read()
    
    async def delete(self, endpoint: str) -> Dict[str, Any]:
        """
        Make DELETE request to ElevenLabs API.
        
        Args:
            endpoint: API endpoint path
            
        Returns:
            JSON response data
        """
        response = await self._make_request_with_retry("DELETE", endpoint)
        return await response.json()
    
    async def close(self):
        """Close the HTTP session and cleanup resources."""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
    
    def get_rate_limit_status(self) -> Optional[RateLimitInfo]:
        """
        Get current rate limit information.
        
        Returns:
            RateLimitInfo object or None if no rate limit data available
        """
        return self.rate_limit_info
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check by calling ElevenLabs user info endpoint.
        
        Returns:
            Health check result with user info
            
        Raises:
            ElevenLabsError: If health check fails
        """
        try:
            user_info = await self.get("/user")
            return {
                "status": "healthy",
                "user_id": user_info.get("xi_api_key", "unknown"),
                "subscription": user_info.get("subscription", {}),
                "rate_limit": self.rate_limit_info.__dict__ if self.rate_limit_info else None
            }
        except Exception as e:
            logger.error(f"ElevenLabs health check failed: {e}")
            raise ElevenLabsError(f"Health check failed: {e}")