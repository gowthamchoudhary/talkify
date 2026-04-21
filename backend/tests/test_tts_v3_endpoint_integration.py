"""
Integration tests for TTS v3 endpoint with proper mocking.
"""
import pytest
import os
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient


class TestTTSv3EndpointIntegration:
    """Integration tests for the /api/speak endpoint."""
    
    @pytest.fixture
    def mock_env_vars(self):
        """Mock environment variables for testing."""
        with patch.dict(os.environ, {
            'ELEVENLABS_API_KEY': 'test_api_key_12345',
            'GEMINI_API_KEY': 'test_gemini_key_12345'
        }):
            yield
    
    @pytest.fixture
    def client(self, mock_env_vars):
        """Create test client with mocked environment."""
        from main import app
        return TestClient(app)
    
    @pytest.fixture
    def speak_request_data(self):
        """Sample speak request data."""
        return {
            "text": "Hello! I'm excited to meet you!",
            "voice_config": {
                "voice_id": "test_voice_123",
                "style": "playful",
                "settings": {
                    "stability": 0.6,
                    "similarity_boost": 0.7,
                    "style": 0.5
                }
            }
        }
    
    def test_speak_endpoint_with_mocked_service(self, client, speak_request_data):
        """Test speak endpoint with fully mocked ElevenLabs service."""
        with patch('main.ElevenLabsService') as mock_service_class:
            # Create mock service instance
            mock_service = AsyncMock()
            mock_service_class.return_value.__aenter__.return_value = mock_service
            mock_service_class.return_value.__aexit__.return_value = None
            
            # Mock service methods
            mock_audio_data = b"fake_audio_data_12345"
            mock_service.text_to_speech_v3.return_value = mock_audio_data
            mock_service.get_conversation_context.return_value = ["Previous message"]
            mock_service._detect_emotional_tags.return_value = ["excited", "happy"]
            mock_service.add_conversation_message.return_value = None
            
            # Make request
            response = client.post("/api/speak", json=speak_request_data)
            
            # Verify response structure
            assert response.status_code == 200
            data = response.json()
            
            # Check success response
            assert data["success"] is True
            assert data["data"] is not None
            assert data["error"] is None
            
            # Check response data
            response_data = data["data"]
            assert "audio_url" in response_data
            assert "session_id" in response_data
            assert response_data["text"] == speak_request_data["text"]
            assert response_data["voice_id"] == speak_request_data["voice_config"]["voice_id"]
            assert response_data["emotional_tags"] == ["excited", "happy"]
            assert response_data["audio_format"] == "mp3"
            assert response_data["voice_style"] == "playful"
            assert "audio_size_bytes" in response_data
            assert "duration_estimate" in response_data
            
            # Verify service interactions
            mock_service.text_to_speech_v3.assert_called_once()
            mock_service.get_conversation_context.assert_called_once()
            mock_service.add_conversation_message.assert_called_once()
    
    def test_speak_endpoint_service_error_handling(self, client, speak_request_data):
        """Test error handling when ElevenLabs service fails."""
        with patch('main.ElevenLabsService') as mock_service_class:
            # Mock service that raises an error
            mock_service = AsyncMock()
            mock_service_class.return_value.__aenter__.return_value = mock_service
            
            # Import and use the actual exception
            from src.exceptions import ElevenLabsError
            mock_service.text_to_speech_v3.side_effect = ElevenLabsError("API rate limit exceeded")
            mock_service.get_conversation_context.return_value = []
            
            # Make request
            response = client.post("/api/speak", json=speak_request_data)
            
            # Verify error response
            assert response.status_code == 200  # FastAPI returns 200 with error in body
            data = response.json()
            
            assert data["success"] is False
            assert data["data"] is None
            assert data["error"] is not None
            assert data["error"]["code"] == "TTS_ERROR"
            assert "API rate limit exceeded" in data["error"]["message"]
    
    def test_speak_endpoint_request_validation(self, client):
        """Test request validation for the speak endpoint."""
        # Test with invalid voice style
        invalid_request = {
            "text": "Hello world!",
            "voice_config": {
                "voice_id": "test_voice",
                "style": "invalid_style",  # Invalid style
                "settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5,
                    "style": 0.0
                }
            }
        }
        
        response = client.post("/api/speak", json=invalid_request)
        assert response.status_code == 422  # Validation error
        
        # Test with empty text
        empty_text_request = {
            "text": "",  # Empty text should fail validation
            "voice_config": {
                "voice_id": "test_voice",
                "style": "warm",
                "settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5,
                    "style": 0.0
                }
            }
        }
        
        response = client.post("/api/speak", json=empty_text_request)
        assert response.status_code == 422  # Validation error
    
    def test_speak_endpoint_voice_settings_validation(self, client):
        """Test voice settings validation in the request."""
        # Test with invalid voice settings (out of range)
        invalid_settings_request = {
            "text": "Hello world!",
            "voice_config": {
                "voice_id": "test_voice",
                "style": "warm",
                "settings": {
                    "stability": 1.5,  # > 1.0, should fail
                    "similarity_boost": 0.5,
                    "style": 0.0
                }
            }
        }
        
        response = client.post("/api/speak", json=invalid_settings_request)
        assert response.status_code == 422  # Validation error
    
    def test_health_check_with_api_keys(self, client):
        """Test that health check works with mocked API keys."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"  # Should be healthy with mocked keys
        assert data["checks"]["elevenlabs_api_key"] == "configured"
        assert data["checks"]["gemini_api_key"] == "configured"
    
    def test_voice_styles_endpoint(self, client):
        """Test the voice styles endpoint works."""
        with patch('main.VoiceDesigner') as mock_designer_class:
            mock_designer = AsyncMock()
            mock_designer_class.return_value.__aenter__.return_value = mock_designer
            
            # Mock voice options
            mock_voice_options = [
                {
                    "style": "mysterious",
                    "name": "Mysterious",
                    "description": "A mysterious voice with enigmatic, secretive, deep characteristics",
                    "keywords": ["enigmatic", "secretive", "deep", "haunting", "whispered"]
                },
                {
                    "style": "playful",
                    "name": "Playful", 
                    "description": "A playful voice with energetic, cheerful, lively characteristics",
                    "keywords": ["energetic", "cheerful", "lively", "fun", "animated"]
                }
            ]
            mock_designer.get_voice_options.return_value = mock_voice_options
            
            response = client.get("/api/voice/styles")
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True
            assert "voice_styles" in data["data"]
            assert len(data["data"]["voice_styles"]) == 2


if __name__ == "__main__":
    pytest.main([__file__])