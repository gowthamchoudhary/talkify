"""
Tests for the /api/speak endpoint implementation.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from src.models import SpeakRequest, VoiceConfig, VoiceStyle


class TestSpeakEndpoint:
    """Test the /api/speak endpoint functionality."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
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
    
    @pytest.mark.asyncio
    async def test_speak_endpoint_success(self, client, speak_request_data):
        """Test successful text-to-speech conversion."""
        with patch('main.ElevenLabsService') as mock_service_class:
            # Mock the service
            mock_service = AsyncMock()
            mock_service_class.return_value.__aenter__.return_value = mock_service
            
            # Mock TTS v3 response
            mock_audio_data = b"fake_audio_data_12345"
            mock_service.text_to_speech_v3.return_value = mock_audio_data
            mock_service.get_conversation_context.return_value = []
            mock_service._detect_emotional_tags.return_value = ["excited", "happy"]
            
            # Make request
            response = client.post("/api/speak", json=speak_request_data)
            
            # Debug: print actual response
            print("Response status:", response.status_code)
            print("Response body:", response.json())
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert "audio_url" in data["data"]
            assert data["data"]["text"] == speak_request_data["text"]
            assert data["data"]["voice_id"] == speak_request_data["voice_config"]["voice_id"]
            assert data["data"]["emotional_tags"] == ["excited", "happy"]
            assert data["data"]["audio_format"] == "mp3"
            assert data["data"]["voice_style"] == "playful"
    
    def test_speak_endpoint_invalid_request(self, client):
        """Test speak endpoint with invalid request data."""
        # Missing required fields
        invalid_data = {
            "text": "",  # Empty text
            "voice_config": {
                "voice_id": "",  # Empty voice ID
                "style": "invalid_style",  # Invalid style
                "settings": {}
            }
        }
        
        response = client.post("/api/speak", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    def test_speak_endpoint_missing_text(self, client):
        """Test speak endpoint with missing text field."""
        invalid_data = {
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
        
        response = client.post("/api/speak", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_speak_endpoint_service_error(self, client, speak_request_data):
        """Test speak endpoint when ElevenLabs service fails."""
        with patch('src.services.elevenlabs_service.ElevenLabsService') as mock_service_class:
            # Mock service that raises an error
            mock_service = AsyncMock()
            mock_service_class.return_value.__aenter__.return_value = mock_service
            
            from src.exceptions import ElevenLabsError
            mock_service.text_to_speech_v3.side_effect = ElevenLabsError("API Error")
            mock_service.get_conversation_context.return_value = []
            
            # Make request
            response = client.post("/api/speak", json=speak_request_data)
            
            # Verify error response
            assert response.status_code == 200  # FastAPI returns 200 with error in body
            data = response.json()
            
            assert data["success"] is False
            assert data["error"]["code"] == "TTS_ERROR"
            assert "API Error" in data["error"]["message"]
    
    def test_speak_request_model_validation(self):
        """Test SpeakRequest model validation."""
        # Valid request
        valid_data = {
            "text": "Hello world!",
            "voice_config": {
                "voice_id": "test_voice_123",
                "style": "warm",
                "settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.6,
                    "style": 0.3
                }
            }
        }
        
        request = SpeakRequest(**valid_data)
        assert request.text == "Hello world!"
        assert request.voice_config.voice_id == "test_voice_123"
        assert request.voice_config.style == VoiceStyle.WARM
    
    def test_speak_request_text_validation(self):
        """Test text validation in SpeakRequest."""
        # Test empty text
        with pytest.raises(ValueError):
            SpeakRequest(
                text="",
                voice_config=VoiceConfig(
                    voice_id="test",
                    style=VoiceStyle.WARM,
                    settings={}
                )
            )
        
        # Test whitespace-only text
        with pytest.raises(ValueError):
            SpeakRequest(
                text="   ",
                voice_config=VoiceConfig(
                    voice_id="test",
                    style=VoiceStyle.WARM,
                    settings={}
                )
            )
        
        # Test text too long
        with pytest.raises(ValueError):
            SpeakRequest(
                text="x" * 1001,  # Exceeds max_length=1000
                voice_config=VoiceConfig(
                    voice_id="test",
                    style=VoiceStyle.WARM,
                    settings={}
                )
            )
    
    @pytest.mark.asyncio
    async def test_speak_endpoint_conversation_context(self, client, speak_request_data):
        """Test that conversation context is used for emotional analysis."""
        with patch('src.services.elevenlabs_service.ElevenLabsService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value.__aenter__.return_value = mock_service
            
            # Mock conversation context
            mock_context = ["I'm feeling happy today!", "This is wonderful!"]
            mock_service.get_conversation_context.return_value = mock_context
            mock_service.text_to_speech_v3.return_value = b"audio_data"
            mock_service._detect_emotional_tags.return_value = ["happy", "excited"]
            
            # Make request
            response = client.post("/api/speak", json=speak_request_data)
            
            # Verify context was used
            assert response.status_code == 200
            mock_service.get_conversation_context.assert_called_once()
            
            # Verify TTS was called with context
            call_args = mock_service.text_to_speech_v3.call_args
            assert call_args[1]["conversation_context"] == mock_context
            
            # Verify message was added to context
            mock_service.add_conversation_message.assert_called_once()
    
    def test_voice_config_validation(self):
        """Test VoiceConfig model validation."""
        # Valid config
        config = VoiceConfig(
            voice_id="test_voice",
            style=VoiceStyle.MYSTERIOUS,
            settings={
                "stability": 0.7,
                "similarity_boost": 0.6,
                "style": 0.8
            }
        )
        assert config.voice_id == "test_voice"
        assert config.style == VoiceStyle.MYSTERIOUS
        
        # Test invalid settings ranges
        with pytest.raises(ValueError):
            VoiceConfig(
                voice_id="test",
                style=VoiceStyle.WARM,
                settings={
                    "stability": 1.5,  # > 1.0
                    "similarity_boost": 0.5,
                    "style": 0.3
                }
            )
        
        with pytest.raises(ValueError):
            VoiceConfig(
                voice_id="test",
                style=VoiceStyle.WARM,
                settings={
                    "stability": 0.5,
                    "similarity_boost": -0.1,  # < 0.0
                    "style": 0.3
                }
            )


if __name__ == "__main__":
    pytest.main([__file__])