"""
Tests for validation utilities.
"""
import pytest
from src.validation import (
    validate_image_file,
    validate_api_key_format,
    validate_session_id,
    validate_audio_url,
    sanitize_text_input,
    create_error_response,
    _validate_image_signature
)
from src.exceptions import ValidationError, FileUploadError, VoiceSnapException


class TestImageFileValidation:
    """Test image file validation."""
    
    def test_valid_jpeg_file(self):
        """Test valid JPEG file validation."""
        # JPEG signature: FF D8 FF
        jpeg_content = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01' + b'x' * 100
        validate_image_file(jpeg_content, "test.jpg", "image/jpeg")
    
    def test_valid_png_file(self):
        """Test valid PNG file validation."""
        # PNG signature: 89 50 4E 47 0D 0A 1A 0A
        png_content = b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a' + b'x' * 100
        validate_image_file(png_content, "test.png", "image/png")
    
    def test_valid_webp_file(self):
        """Test valid WebP file validation."""
        # WebP signature: RIFF....WEBP
        webp_content = b'RIFF\x00\x00\x00\x00WEBP' + b'x' * 100
        validate_image_file(webp_content, "test.webp", "image/webp")
    
    def test_empty_file(self):
        """Test empty file rejection."""
        with pytest.raises(FileUploadError, match="File is empty"):
            validate_image_file(b'', "test.jpg", "image/jpeg")
    
    def test_invalid_mime_type(self):
        """Test invalid MIME type rejection."""
        content = b'x' * 100
        with pytest.raises(ValidationError, match="Invalid file format"):
            validate_image_file(content, "test.txt", "text/plain")
    
    def test_file_too_large(self):
        """Test file size limit enforcement."""
        # Create content larger than default max size (10MB)
        large_content = b'x' * (11 * 1024 * 1024)  # 11MB
        with pytest.raises(FileUploadError, match="exceeds maximum allowed size"):
            validate_image_file(large_content, "test.jpg", "image/jpeg")
    
    def test_invalid_file_signature(self):
        """Test file signature validation."""
        # Content that doesn't match JPEG signature
        invalid_content = b'not a jpeg file content'
        with pytest.raises(ValidationError, match="File content does not match"):
            validate_image_file(invalid_content, "test.jpg", "image/jpeg")


class TestImageSignatureValidation:
    """Test image signature validation."""
    
    def test_jpeg_signature(self):
        """Test JPEG signature validation."""
        valid_jpeg = b'\xff\xd8\xff\xe0' + b'x' * 10
        assert _validate_image_signature(valid_jpeg, "image/jpeg") is True
        
        invalid_jpeg = b'not jpeg'
        assert _validate_image_signature(invalid_jpeg, "image/jpeg") is False
    
    def test_png_signature(self):
        """Test PNG signature validation."""
        valid_png = b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a' + b'x' * 10
        assert _validate_image_signature(valid_png, "image/png") is True
        
        invalid_png = b'not png'
        assert _validate_image_signature(invalid_png, "image/png") is False
    
    def test_webp_signature(self):
        """Test WebP signature validation."""
        valid_webp = b'RIFF\x00\x00\x00\x00WEBP' + b'x' * 10
        assert _validate_image_signature(valid_webp, "image/webp") is True
        
        invalid_webp = b'not webp'
        assert _validate_image_signature(invalid_webp, "image/webp") is False
    
    def test_unknown_type(self):
        """Test unknown type returns True."""
        content = b'any content'
        assert _validate_image_signature(content, "image/unknown") is True


class TestAPIKeyValidation:
    """Test API key validation."""
    
    def test_valid_api_key(self):
        """Test valid API key."""
        validate_api_key_format("sk-1234567890abcdef", "ElevenLabs")
    
    def test_empty_api_key(self):
        """Test empty API key rejection."""
        with pytest.raises(ValidationError, match="API key is required"):
            validate_api_key_format("", "ElevenLabs")
        
        with pytest.raises(ValidationError, match="API key is required"):
            validate_api_key_format("   ", "ElevenLabs")
    
    def test_short_api_key(self):
        """Test short API key rejection."""
        with pytest.raises(ValidationError, match="appears to be too short"):
            validate_api_key_format("short", "ElevenLabs")
    
    def test_placeholder_api_key(self):
        """Test placeholder API key rejection."""
        placeholders = ["your_api_key", "api_key_here", "replace_me", "test", "demo"]
        for placeholder in placeholders:
            with pytest.raises(ValidationError, match="appears to be a placeholder"):
                validate_api_key_format(placeholder, "ElevenLabs")


class TestSessionValidation:
    """Test session ID validation."""
    
    def test_valid_session_id(self):
        """Test valid session ID."""
        validate_session_id("session_12345678")
        validate_session_id("sess-abc-123-def")
        validate_session_id("abcdef1234567890")
    
    def test_empty_session_id(self):
        """Test empty session ID rejection."""
        with pytest.raises(ValidationError, match="Session ID is required"):
            validate_session_id("")
        
        with pytest.raises(ValidationError, match="Session ID is required"):
            validate_session_id("   ")
    
    def test_session_id_length(self):
        """Test session ID length validation."""
        # Too short
        with pytest.raises(ValidationError, match="must be between 8 and 128 characters"):
            validate_session_id("short")
        
        # Too long
        long_id = "x" * 129
        with pytest.raises(ValidationError, match="must be between 8 and 128 characters"):
            validate_session_id(long_id)
    
    def test_session_id_invalid_characters(self):
        """Test session ID character validation."""
        with pytest.raises(ValidationError, match="contains invalid characters"):
            validate_session_id("session@123!")


class TestAudioURLValidation:
    """Test audio URL validation."""
    
    def test_valid_audio_url(self):
        """Test valid audio URL."""
        validate_audio_url("https://example.com/audio.mp3")
        validate_audio_url("http://localhost:8000/audio.wav")
    
    def test_empty_audio_url(self):
        """Test empty audio URL rejection."""
        with pytest.raises(ValidationError, match="Audio URL is required"):
            validate_audio_url("")
        
        with pytest.raises(ValidationError, match="Audio URL is required"):
            validate_audio_url("   ")
    
    def test_invalid_audio_url_protocol(self):
        """Test invalid URL protocol rejection."""
        with pytest.raises(ValidationError, match="must start with http"):
            validate_audio_url("ftp://example.com/audio.mp3")
        
        with pytest.raises(ValidationError, match="must start with http"):
            validate_audio_url("example.com/audio.mp3")
    
    def test_audio_url_too_long(self):
        """Test audio URL length limit."""
        long_url = "https://example.com/" + "x" * 2050
        with pytest.raises(ValidationError, match="Audio URL is too long"):
            validate_audio_url(long_url)


class TestTextSanitization:
    """Test text input sanitization."""
    
    def test_valid_text(self):
        """Test valid text sanitization."""
        result = sanitize_text_input("Hello world!")
        assert result == "Hello world!"
    
    def test_text_whitespace_trimming(self):
        """Test whitespace trimming."""
        result = sanitize_text_input("  Hello world!  ")
        assert result == "Hello world!"
    
    def test_empty_text(self):
        """Test empty text rejection."""
        with pytest.raises(ValidationError, match="Text input is required"):
            sanitize_text_input("")
        
        with pytest.raises(ValidationError, match="cannot be empty or just whitespace"):
            sanitize_text_input("   ")
    
    def test_text_too_long(self):
        """Test text length limit."""
        long_text = "x" * 1001
        with pytest.raises(ValidationError, match="exceeds maximum length"):
            sanitize_text_input(long_text, max_length=1000)
    
    def test_text_character_cleaning(self):
        """Test problematic character removal."""
        dirty_text = "Hello\x00world\r\ntest\rend"
        result = sanitize_text_input(dirty_text)
        assert result == "Helloworld\ntest\nend"


class TestErrorResponseCreation:
    """Test error response creation."""
    
    def test_voicesnap_exception_response(self):
        """Test VoiceSnapException error response."""
        error = VoiceSnapException(
            message="Test error",
            code="TEST_ERROR",
            status_code=400,
            details={"field": "test"}
        )
        
        response = create_error_response(error, "req_123")
        
        assert response["success"] is False
        assert response["error"]["code"] == "TEST_ERROR"
        assert response["error"]["message"] == "Test error"
        assert response["error"]["details"]["field"] == "test"
        assert response["request_id"] == "req_123"
        assert "timestamp" in response
    
    def test_generic_exception_response(self):
        """Test generic exception error response."""
        error = ValueError("Generic error")
        
        response = create_error_response(error)
        
        assert response["success"] is False
        assert response["error"]["code"] == "INTERNAL_ERROR"
        assert response["error"]["message"] == "An unexpected error occurred"
        assert response["error"]["details"]["error_type"] == "ValueError"
        assert "timestamp" in response
    
    def test_validation_error_response(self):
        """Test ValidationError response."""
        error = ValidationError("Invalid input", field="name")
        
        response = create_error_response(error)
        
        assert response["success"] is False
        assert response["error"]["code"] == "VALIDATION_ERROR"
        assert response["error"]["details"]["field"] == "name"


class TestIntegratedValidation:
    """Test integrated validation scenarios."""
    
    def test_complete_file_upload_validation(self):
        """Test complete file upload validation flow."""
        # Valid JPEG file
        jpeg_content = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01' + b'test content'
        
        # Should not raise any exceptions
        validate_image_file(jpeg_content, "photo.jpg", "image/jpeg")
    
    def test_api_integration_validation(self):
        """Test API integration validation."""
        # Valid API key
        validate_api_key_format("sk-abcdef1234567890", "ElevenLabs")
        
        # Valid session
        validate_session_id("session_abc123def456")
        
        # Valid audio URL
        validate_audio_url("https://api.elevenlabs.io/audio/response.mp3")
        
        # Valid text
        text = sanitize_text_input("Hello, I'm a friendly AI character!")
        assert text == "Hello, I'm a friendly AI character!"