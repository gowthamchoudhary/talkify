"""
Validation utilities for Talkify API.
"""
from typing import List, Dict, Any, Optional
import mimetypes
from src.exceptions import ValidationError, FileUploadError
from src.config import settings


def validate_image_file(file_content: bytes, filename: str, content_type: Optional[str] = None) -> None:
    """
    Validate uploaded image file format and size.
    
    Args:
        file_content: The file content as bytes
        filename: Original filename
        content_type: MIME content type (optional)
    
    Raises:
        FileUploadError: If file validation fails
        ValidationError: If file format is invalid
    """
    # Check file size
    if len(file_content) > settings.max_file_size:
        raise FileUploadError(
            f"File size {len(file_content)} bytes exceeds maximum allowed size {settings.max_file_size} bytes",
            file_type=content_type
        )
    
    # Check file is not empty
    if len(file_content) == 0:
        raise FileUploadError("File is empty", file_type=content_type)
    
    # Determine MIME type from filename if not provided
    if not content_type:
        content_type, _ = mimetypes.guess_type(filename)
    
    # Validate MIME type
    if content_type not in settings.allowed_image_types:
        raise ValidationError(
            f"Invalid file format '{content_type}'. Allowed formats: {', '.join(settings.allowed_image_types)}",
            field="file_type"
        )
    
    # Basic file signature validation for common image formats
    if not _validate_image_signature(file_content, content_type):
        raise ValidationError(
            f"File content does not match declared type '{content_type}'",
            field="file_content"
        )


def _validate_image_signature(file_content: bytes, content_type: str) -> bool:
    """
    Validate file signature matches the declared MIME type.
    
    Args:
        file_content: The file content as bytes
        content_type: Declared MIME content type
    
    Returns:
        bool: True if signature matches, False otherwise
    """
    if len(file_content) < 8:
        return False
    
    # Check file signatures (magic numbers)
    signatures = {
        'image/jpeg': [b'\xff\xd8\xff'],
        'image/png': [b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a'],
        'image/webp': [b'RIFF', b'WEBP']  # WebP has RIFF header followed by WEBP
    }
    
    if content_type not in signatures:
        return True  # Unknown type, assume valid
    
    for signature in signatures[content_type]:
        if content_type == 'image/webp':
            # Special case for WebP: check for RIFF at start and WEBP at offset 8
            if file_content.startswith(b'RIFF') and file_content[8:12] == b'WEBP':
                return True
        else:
            if file_content.startswith(signature):
                return True
    
    return False


def validate_api_key_format(api_key: str, service_name: str) -> None:
    """
    Validate API key format for external services.
    
    Args:
        api_key: The API key to validate
        service_name: Name of the service (for error messages)
    
    Raises:
        ValidationError: If API key format is invalid
    """
    if not api_key or not api_key.strip():
        raise ValidationError(f"{service_name} API key is required", field="api_key")
    
    # Check for common placeholder values
    placeholder_values = ["your_api_key", "api_key_here", "replace_me", "test", "demo"]
    if api_key.lower().strip() in placeholder_values:
        raise ValidationError(f"{service_name} API key appears to be a placeholder value", field="api_key")
    
    # Basic format validation - API keys should be reasonable length
    if len(api_key.strip()) < 10:
        raise ValidationError(f"{service_name} API key appears to be too short", field="api_key")


def validate_session_id(session_id: str) -> None:
    """
    Validate session ID format.
    
    Args:
        session_id: Session identifier to validate
    
    Raises:
        ValidationError: If session ID is invalid
    """
    if not session_id or not session_id.strip():
        raise ValidationError("Session ID is required", field="session_id")
    
    # Session IDs should be reasonable length and contain valid characters
    session_id = session_id.strip()
    if len(session_id) < 8 or len(session_id) > 128:
        raise ValidationError("Session ID must be between 8 and 128 characters", field="session_id")
    
    # Allow alphanumeric, hyphens, and underscores
    if not session_id.replace('-', '').replace('_', '').isalnum():
        raise ValidationError("Session ID contains invalid characters", field="session_id")


def validate_audio_url(url: str) -> None:
    """
    Validate audio URL format.
    
    Args:
        url: Audio URL to validate
    
    Raises:
        ValidationError: If URL is invalid
    """
    if not url or not url.strip():
        raise ValidationError("Audio URL is required", field="audio_url")
    
    url = url.strip()
    
    # Basic URL format validation
    if not (url.startswith('http://') or url.startswith('https://')):
        raise ValidationError("Audio URL must start with http:// or https://", field="audio_url")
    
    # Check for reasonable URL length
    if len(url) > 2048:
        raise ValidationError("Audio URL is too long", field="audio_url")


def sanitize_text_input(text: str, max_length: int = 1000) -> str:
    """
    Sanitize and validate text input.
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
    
    Returns:
        str: Sanitized text
    
    Raises:
        ValidationError: If text is invalid
    """
    if not text:
        raise ValidationError("Text input is required", field="text")
    
    # Strip whitespace
    text = text.strip()
    
    if not text:
        raise ValidationError("Text cannot be empty or just whitespace", field="text")
    
    if len(text) > max_length:
        raise ValidationError(f"Text exceeds maximum length of {max_length} characters", field="text")
    
    # Remove any null bytes or other problematic characters
    text = text.replace('\x00', '')
    
    # Normalize line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    return text


def create_error_response(error: Exception, request_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Create standardized error response from exception.
    
    Args:
        error: Exception to convert to response
        request_id: Optional request identifier
    
    Returns:
        Dict containing standardized error response
    """
    from src.exceptions import TalkifyException
    
    if isinstance(error, TalkifyException):
        return {
            "success": False,
            "error": {
                "code": error.code,
                "message": error.message,
                "details": error.details
            },
            "request_id": request_id,
            "timestamp": __import__('time').time()
        }
    else:
        # Generic error handling
        return {
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": {"error_type": type(error).__name__}
            },
            "request_id": request_id,
            "timestamp": __import__('time').time()
        }