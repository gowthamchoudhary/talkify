"""
Custom exception classes for VoiceSnap API.
"""
from typing import Optional, Dict, Any


class VoiceSnapException(Exception):
    """Base exception for VoiceSnap application."""
    
    def __init__(
        self, 
        message: str, 
        code: str = "VOICESNAP_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class APIError(VoiceSnapException):
    """Base class for external API errors."""
    
    def __init__(
        self, 
        service: str, 
        message: str, 
        status_code: int = 500,
        api_status_code: Optional[int] = None
    ):
        self.service = service
        self.api_status_code = api_status_code
        super().__init__(
            message=f"{service} API error: {message}",
            code=f"{service.upper()}_API_ERROR",
            status_code=status_code,
            details={"service": service, "api_status_code": api_status_code}
        )


class ElevenLabsError(APIError):
    """Specific error handling for ElevenLabs API issues."""
    
    def __init__(self, message: str, api_status_code: Optional[int] = None):
        super().__init__(
            service="ElevenLabs",
            message=message,
            status_code=502,  # Bad Gateway for external service errors
            api_status_code=api_status_code
        )


class GeminiError(APIError):
    """Specific error handling for Google Gemini API issues."""
    
    def __init__(self, message: str, api_status_code: Optional[int] = None):
        super().__init__(
            service="Gemini",
            message=message,
            status_code=502,  # Bad Gateway for external service errors
            api_status_code=api_status_code
        )


class ValidationError(VoiceSnapException):
    """Error for input validation failures."""
    
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=400,
            details={"field": field} if field else {}
        )


class FileUploadError(VoiceSnapException):
    """Error for file upload issues."""
    
    def __init__(self, message: str, file_type: Optional[str] = None):
        super().__init__(
            message=message,
            code="FILE_UPLOAD_ERROR",
            status_code=400,
            details={"file_type": file_type} if file_type else {}
        )


class SessionError(VoiceSnapException):
    """Error for session management issues."""
    
    def __init__(self, message: str, session_id: Optional[str] = None):
        super().__init__(
            message=message,
            code="SESSION_ERROR",
            status_code=400,
            details={"session_id": session_id} if session_id else {}
        )