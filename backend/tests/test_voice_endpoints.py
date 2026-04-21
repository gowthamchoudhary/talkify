"""
Tests for Voice Design API endpoints.

Tests the voice design endpoints in main.py to ensure proper integration
with the VoiceDesigner service.
"""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from main import app
from src.models import ObjectProfile, VoiceStyle, VoiceConfig


@pytest.fixture
def client():
    """Create test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture
def sample_profile_data():
    """Sample object profile data for testing."""
    return {
        "id": "test-profile-001",
        "name": "Whiskers",
        "species": "Tabby Cat",
        "emoji": "🐱",
        "traits": ["Curious", "Playful", "Wise"],
        "backstory": "A mysterious tabby cat who has lived in the old library for years."
    }


class TestVoiceStylesEndpoint:
    """Test cases for /api/voice/styles endpoint."""
    
    def test_get_voice_styles_success(self, client):
        """Test successful retrieval of voice styles."""
        with patch('main.VoiceDesigner') as mock_designer_class:
            # Mock the designer instance and its methods
            mock_designer = AsyncMock()
            mock_designer.get_voice_options.return_value = [
                {
                    "style": "mysterious",
                    "name": "Mysterious",
                    "description": "A mysterious and enigmatic voice",
                    "keywords": ["enigmatic", "secretive", "deep"]
                },
                {
                    "style": "warm",
                    "name": "Warm", 
                    "description": "A warm and comforting voice",
                    "keywords": ["friendly", "caring", "gentle"]
                }
            ]
            
            # Configure the async context manager
            mock_designer_class.return_value.__aenter__.return_value = mock_designer
            mock_designer_class.return_value.__aexit__.return_value = None
            
            response = client.get("/api/voice/styles")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "voice_styles" in data["data"]
            assert len(data["data"]["voice_styles"]) == 2
    
    def test_get_voice_styles_error(self, client):
        """Test voice styles endpoint with service error."""
        with patch('main.VoiceDesigner') as mock_designer_class:
            mock_designer_class.side_effect = Exception("Service unavailable")
            
            response = client.get("/api/voice/styles")
            
            assert response.status_code == 200  # API returns 200 with error in body
            data = response.json()
            assert data["success"] is False
            assert "error" in data


class TestVoiceCreateEndpoint:
    """Test cases for /api/voice/create endpoint."""
    
    def test_create_voice_success(self, client, sample_profile_data):
        """Test successful voice creation."""
        with patch('main.VoiceDesigner') as mock_designer_class:
            # Mock the designer instance
            mock_designer = AsyncMock()
            mock_designer.recommend_voice_style.return_value = VoiceStyle.MYSTERIOUS
            mock_designer.create_voice.return_value = VoiceConfig(
                voice_id="test-voice-123",
                style=VoiceStyle.MYSTERIOUS,
                settings={"stability": 0.75, "similarity_boost": 0.65}
            )
            mock_designer.store_voice_config = AsyncMock()
            
            # Configure the async context manager
            mock_designer_class.return_value.__aenter__.return_value = mock_designer
            mock_designer_class.return_value.__aexit__.return_value = None
            
            response = client.post("/api/voice/create", json=sample_profile_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "voice_config" in data["data"]
            assert "session_id" in data["data"]
            assert data["data"]["voice_config"]["voice_id"] == "test-voice-123"
    
    def test_create_voice_with_specific_style(self, client, sample_profile_data):
        """Test voice creation with specific style parameter."""
        request_data = {
            **sample_profile_data,
            "style": "playful"
        }
        
        with patch('main.VoiceDesigner') as mock_designer_class:
            mock_designer = AsyncMock()
            mock_designer.create_voice.return_value = VoiceConfig(
                voice_id="test-voice-456",
                style=VoiceStyle.PLAYFUL,
                settings={"stability": 0.45, "similarity_boost": 0.85}
            )
            mock_designer.store_voice_config = AsyncMock()
            
            mock_designer_class.return_value.__aenter__.return_value = mock_designer
            mock_designer_class.return_value.__aexit__.return_value = None
            
            response = client.post("/api/voice/create", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["voice_config"]["voice_id"] == "test-voice-456"
    
    def test_create_voice_elevenlabs_error(self, client, sample_profile_data):
        """Test voice creation with ElevenLabs API error."""
        from src.exceptions import ElevenLabsError
        
        with patch('main.VoiceDesigner') as mock_designer_class:
            mock_designer = AsyncMock()
            mock_designer.recommend_voice_style.return_value = VoiceStyle.WARM
            mock_designer.create_voice.side_effect = ElevenLabsError("API rate limit exceeded")
            
            mock_designer_class.return_value.__aenter__.return_value = mock_designer
            mock_designer_class.return_value.__aexit__.return_value = None
            
            response = client.post("/api/voice/create", json=sample_profile_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert data["error"]["code"] == "VOICE_CREATION_ERROR"
            assert "rate limit" in data["error"]["message"]
    
    def test_create_voice_invalid_profile(self, client):
        """Test voice creation with invalid profile data."""
        invalid_profile = {
            "id": "test",
            "name": "",  # Invalid: empty name
            "species": "Cat",
            "emoji": "🐱",
            "traits": ["Curious"],  # Invalid: not exactly 3 traits
            "backstory": "Short"
        }
        
        response = client.post("/api/voice/create", json=invalid_profile)
        
        # Should return validation error
        assert response.status_code == 422


class TestVoiceRecommendEndpoint:
    """Test cases for /api/voice/recommend endpoint."""
    
    def test_recommend_voice_style_success(self, client):
        """Test successful voice style recommendation."""
        with patch('main.VoiceDesigner') as mock_designer_class:
            mock_designer = AsyncMock()
            mock_designer.recommend_voice_style.return_value = VoiceStyle.PLAYFUL
            mock_designer.get_voice_options.return_value = [
                {
                    "style": "playful",
                    "name": "Playful",
                    "description": "A playful and energetic voice",
                    "keywords": ["energetic", "fun", "lively"]
                }
            ]
            
            mock_designer_class.return_value.__aenter__.return_value = mock_designer
            mock_designer_class.return_value.__aexit__.return_value = None
            
            response = client.get("/api/voice/recommend/toy?traits=playful,energetic,fun")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["recommended_style"] == "playful"
            assert data["data"]["object_type"] == "toy"
            assert "playful" in data["data"]["traits"]
    
    def test_recommend_voice_style_no_traits(self, client):
        """Test voice recommendation without traits (should use defaults)."""
        with patch('main.VoiceDesigner') as mock_designer_class:
            mock_designer = AsyncMock()
            mock_designer.recommend_voice_style.return_value = VoiceStyle.WARM
            mock_designer.get_voice_options.return_value = [
                {
                    "style": "warm",
                    "name": "Warm",
                    "description": "A warm and comforting voice",
                    "keywords": ["friendly", "caring", "gentle"]
                }
            ]
            
            mock_designer_class.return_value.__aenter__.return_value = mock_designer
            mock_designer_class.return_value.__aexit__.return_value = None
            
            response = client.get("/api/voice/recommend/book")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["recommended_style"] == "warm"
            assert data["data"]["object_type"] == "book"
            # Should have default traits
            assert len(data["data"]["traits"]) == 3
    
    def test_recommend_voice_style_error(self, client):
        """Test voice recommendation with service error."""
        with patch('main.VoiceDesigner') as mock_designer_class:
            mock_designer_class.side_effect = Exception("Service error")
            
            response = client.get("/api/voice/recommend/cat?traits=curious")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert data["error"]["code"] == "RECOMMENDATION_ERROR"


class TestVoiceEndpointsIntegration:
    """Integration tests for voice endpoints."""
    
    def test_complete_voice_workflow(self, client, sample_profile_data):
        """Test complete workflow: get styles -> create voice."""
        with patch('main.VoiceDesigner') as mock_designer_class:
            mock_designer = AsyncMock()
            
            # Mock get_voice_options for styles endpoint
            mock_designer.get_voice_options.return_value = [
                {"style": "mysterious", "name": "Mysterious"},
                {"style": "warm", "name": "Warm"}
            ]
            
            # Mock voice creation
            mock_designer.recommend_voice_style.return_value = VoiceStyle.MYSTERIOUS
            mock_designer.create_voice.return_value = VoiceConfig(
                voice_id="workflow-voice-789",
                style=VoiceStyle.MYSTERIOUS,
                settings={"stability": 0.75}
            )
            mock_designer.store_voice_config = AsyncMock()
            
            mock_designer_class.return_value.__aenter__.return_value = mock_designer
            mock_designer_class.return_value.__aexit__.return_value = None
            
            # Step 1: Get available styles
            styles_response = client.get("/api/voice/styles")
            assert styles_response.status_code == 200
            styles_data = styles_response.json()
            assert styles_data["success"] is True
            
            # Step 2: Create voice
            create_response = client.post("/api/voice/create", json=sample_profile_data)
            assert create_response.status_code == 200
            create_data = create_response.json()
            assert create_data["success"] is True
            assert create_data["data"]["voice_config"]["voice_id"] == "workflow-voice-789"


if __name__ == "__main__":
    pytest.main([__file__])