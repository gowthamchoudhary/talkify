"""
Tests for Ambient Sound API endpoints.

Tests the ambient sound endpoints in main.py to ensure proper integration
with ElevenLabs Sound Effects API and correct response formatting.
"""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    """Create test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture
def sample_ambient_request():
    """Sample ambient request data for testing."""
    return {
        "object_type": "forest",
        "intensity": 0.5
    }


@pytest.fixture
def mock_ambient_audio():
    """Mock ambient audio data for testing."""
    return b"mock_ambient_audio_data_for_testing"


class TestAmbientSoundsEndpoint:
    """Test cases for /api/ambient endpoint."""
    
    def test_generate_ambient_sounds_success(self, client, sample_ambient_request, mock_ambient_audio):
        """Test successful ambient sound generation."""
        with patch('src.services.elevenlabs_service.ElevenLabsService') as mock_service_class:
            # Setup mock service
            mock_service = AsyncMock()
            mock_service_class.return_value.__aenter__.return_value = mock_service
            
            # Mock the sound effects generation
            mock_service.generate_sound_effects.return_value = mock_ambient_audio
            mock_service._get_sound_description_for_object.return_value = {
                "primary_description": "Gentle rustling of leaves in a soft breeze",
                "mood": "peaceful",
                "secondary_sounds": ["wind through branches", "bird chirp"]
            }
            
            # Make request
            response = client.post("/api/ambient", json=sample_ambient_request)
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert "data" in data
            
            response_data = data["data"]
            assert response_data["object_type"] == "forest"
            assert response_data["intensity"] == 0.5
            assert response_data["duration_seconds"] == 60
            assert response_data["audio_format"] == "mp3"
            assert response_data["volume_mixed"] is True
            assert response_data["conversation_ready"] is True
            assert "ambient_url" in response_data
            assert "session_id" in response_data
            assert "sound_description" in response_data
            assert "mood" in response_data
            
            # Verify service was called correctly
            mock_service.generate_sound_effects.assert_called_once_with(
                object_type="forest",
                intensity=0.5,
                duration_seconds=60,
                audio_format="mp3"
            )
    
    def test_generate_ambient_sounds_with_different_object_types(self, client, mock_ambient_audio):
        """Test ambient sound generation with various object types."""
        test_objects = ["cat", "ocean", "piano", "book", "unknown_object"]
        
        with patch('src.services.elevenlabs_service.ElevenLabsService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value.__aenter__.return_value = mock_service
            mock_service.generate_sound_effects.return_value = mock_ambient_audio
            mock_service._get_sound_description_for_object.return_value = {
                "primary_description": "Test description",
                "mood": "neutral",
                "secondary_sounds": []
            }
            
            for object_type in test_objects:
                request_data = {"object_type": object_type, "intensity": 0.3}
                response = client.post("/api/ambient", json=request_data)
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["data"]["object_type"] == object_type
    
    def test_generate_ambient_sounds_default_intensity(self, client, mock_ambient_audio):
        """Test ambient sound generation with default intensity."""
        with patch('src.services.elevenlabs_service.ElevenLabsService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value.__aenter__.return_value = mock_service
            mock_service.generate_sound_effects.return_value = mock_ambient_audio
            mock_service._get_sound_description_for_object.return_value = {
                "primary_description": "Test description",
                "mood": "neutral",
                "secondary_sounds": []
            }
            
            # Request without intensity (should use default)
            request_data = {"object_type": "tree"}
            response = client.post("/api/ambient", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            # Should use default intensity of 0.3
            assert data["data"]["intensity"] == 0.3
    
    def test_generate_ambient_sounds_elevenlabs_error(self, client, sample_ambient_request):
        """Test ambient sound generation with ElevenLabs API error."""
        with patch('src.services.elevenlabs_service.ElevenLabsService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value.__aenter__.return_value = mock_service
            
            # Mock ElevenLabs error
            from src.exceptions import ElevenLabsError
            mock_service.generate_sound_effects.side_effect = ElevenLabsError("API rate limit exceeded")
            
            response = client.post("/api/ambient", json=sample_ambient_request)
            
            assert response.status_code == 200  # FastAPI returns 200 with error in response
            data = response.json()
            assert data["success"] is False
            assert data["error"]["code"] == "AMBIENT_GENERATION_ERROR"
            assert "API rate limit exceeded" in data["error"]["message"]
    
    def test_generate_ambient_sounds_invalid_request(self, client):
        """Test ambient sound generation with invalid request data."""
        # Missing required object_type
        invalid_request = {"intensity": 0.5}
        response = client.post("/api/ambient", json=invalid_request)
        
        # Should return validation error
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_generate_ambient_sounds_intensity_bounds(self, client, mock_ambient_audio):
        """Test ambient sound generation with intensity boundary values."""
        with patch('src.services.elevenlabs_service.ElevenLabsService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value.__aenter__.return_value = mock_service
            mock_service.generate_sound_effects.return_value = mock_ambient_audio
            mock_service._get_sound_description_for_object.return_value = {
                "primary_description": "Test description",
                "mood": "neutral",
                "secondary_sounds": []
            }
            
            # Test minimum intensity
            request_data = {"object_type": "test", "intensity": 0.0}
            response = client.post("/api/ambient", json=request_data)
            assert response.status_code == 200
            
            # Test maximum intensity
            request_data = {"object_type": "test", "intensity": 1.0}
            response = client.post("/api/ambient", json=request_data)
            assert response.status_code == 200
            
            # Test invalid intensity (should be caught by Pydantic validation)
            request_data = {"object_type": "test", "intensity": 1.5}
            response = client.post("/api/ambient", json=request_data)
            assert response.status_code == 422  # Validation error


class TestAmbientTypesEndpoint:
    """Test cases for /api/ambient/types endpoint."""
    
    def test_get_available_ambient_types_success(self, client):
        """Test successful retrieval of available ambient types."""
        with patch('src.services.elevenlabs_service.ElevenLabsService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value.__aenter__.return_value = mock_service
            
            # Mock available types
            mock_types = [
                {
                    "object_type": "tree",
                    "description": "Gentle rustling of leaves",
                    "mood": "peaceful",
                    "secondary_sounds": ["wind", "birds"]
                },
                {
                    "object_type": "cat",
                    "description": "Soft purring sounds",
                    "mood": "cozy",
                    "secondary_sounds": ["purr", "breathing"]
                }
            ]
            mock_service.get_available_ambient_types.return_value = mock_types
            
            response = client.get("/api/ambient/types")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert "data" in data
            
            response_data = data["data"]
            assert "available_types" in response_data
            assert response_data["total_count"] == 2
            assert "supported_formats" in response_data
            assert "intensity_range" in response_data
            assert response_data["intensity_range"]["min"] == 0.0
            assert response_data["intensity_range"]["max"] == 1.0
            
            # Verify types structure
            types = response_data["available_types"]
            assert len(types) == 2
            for ambient_type in types:
                assert "object_type" in ambient_type
                assert "description" in ambient_type
                assert "mood" in ambient_type
                assert "secondary_sounds" in ambient_type
    
    def test_get_available_ambient_types_error(self, client):
        """Test ambient types retrieval with service error."""
        with patch('src.services.elevenlabs_service.ElevenLabsService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value.__aenter__.return_value = mock_service
            
            # Mock service error
            mock_service.get_available_ambient_types.side_effect = Exception("Service unavailable")
            
            response = client.get("/api/ambient/types")
            
            assert response.status_code == 200  # FastAPI returns 200 with error in response
            data = response.json()
            assert data["success"] is False
            assert data["error"]["code"] == "AMBIENT_TYPES_ERROR"


class TestContextualAmbientEndpoint:
    """Test cases for /api/ambient/contextual endpoint."""
    
    def test_generate_contextual_ambient_success(self, client, mock_ambient_audio):
        """Test successful contextual ambient sound generation."""
        with patch('src.services.elevenlabs_service.ElevenLabsService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value.__aenter__.return_value = mock_service
            mock_service.create_contextual_ambient_mix.return_value = mock_ambient_audio
            
            # Test with conversation active
            response = client.post(
                "/api/ambient/contextual",
                params={
                    "object_type": "forest",
                    "conversation_active": True,
                    "intensity": 0.5,
                    "duration_seconds": 30
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            response_data = data["data"]
            assert response_data["object_type"] == "forest"
            assert response_data["conversation_active"] is True
            assert response_data["requested_intensity"] == 0.5
            assert response_data["adjusted_intensity"] == 0.3  # 0.5 * 0.6
            assert response_data["duration_seconds"] == 30
            assert response_data["optimization"] == "conversation"
            assert response_data["speech_compatible"] is True
            
            # Verify service was called correctly
            mock_service.create_contextual_ambient_mix.assert_called_once_with(
                object_type="forest",
                conversation_active=True,
                intensity=0.5,
                duration_seconds=30
            )
    
    def test_generate_contextual_ambient_no_conversation(self, client, mock_ambient_audio):
        """Test contextual ambient generation without active conversation."""
        with patch('src.services.elevenlabs_service.ElevenLabsService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value.__aenter__.return_value = mock_service
            mock_service.create_contextual_ambient_mix.return_value = mock_ambient_audio
            
            response = client.post(
                "/api/ambient/contextual",
                params={
                    "object_type": "ocean",
                    "conversation_active": False,
                    "intensity": 0.7
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            response_data = data["data"]
            assert response_data["conversation_active"] is False
            assert response_data["requested_intensity"] == 0.7
            assert response_data["adjusted_intensity"] == 0.7  # No reduction
            assert response_data["optimization"] == "standalone"
    
    def test_generate_contextual_ambient_default_params(self, client, mock_ambient_audio):
        """Test contextual ambient generation with default parameters."""
        with patch('src.services.elevenlabs_service.ElevenLabsService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value.__aenter__.return_value = mock_service
            mock_service.create_contextual_ambient_mix.return_value = mock_ambient_audio
            
            # Only provide required object_type
            response = client.post(
                "/api/ambient/contextual",
                params={"object_type": "piano"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            response_data = data["data"]
            assert response_data["object_type"] == "piano"
            assert response_data["conversation_active"] is False  # Default
            assert response_data["requested_intensity"] == 0.3  # Default
            assert response_data["duration_seconds"] == 60  # Default
    
    def test_generate_contextual_ambient_elevenlabs_error(self, client):
        """Test contextual ambient generation with ElevenLabs error."""
        with patch('src.services.elevenlabs_service.ElevenLabsService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value.__aenter__.return_value = mock_service
            
            from src.exceptions import ElevenLabsError
            mock_service.create_contextual_ambient_mix.side_effect = ElevenLabsError("Generation failed")
            
            response = client.post(
                "/api/ambient/contextual",
                params={"object_type": "test"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert data["error"]["code"] == "CONTEXTUAL_AMBIENT_ERROR"


class TestAmbientEndpointsIntegration:
    """Integration tests for ambient sound endpoints."""
    
    def test_complete_ambient_workflow(self, client, mock_ambient_audio):
        """Test complete ambient sound workflow."""
        with patch('src.services.elevenlabs_service.ElevenLabsService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value.__aenter__.return_value = mock_service
            
            # Setup mocks
            mock_service.get_available_ambient_types.return_value = [
                {"object_type": "forest", "description": "Forest sounds", "mood": "peaceful", "secondary_sounds": []}
            ]
            mock_service.generate_sound_effects.return_value = mock_ambient_audio
            mock_service._get_sound_description_for_object.return_value = {
                "primary_description": "Forest ambiance",
                "mood": "peaceful",
                "secondary_sounds": []
            }
            mock_service.create_contextual_ambient_mix.return_value = mock_ambient_audio
            
            # 1. Get available types
            types_response = client.get("/api/ambient/types")
            assert types_response.status_code == 200
            
            # 2. Generate basic ambient sound
            ambient_request = {"object_type": "forest", "intensity": 0.4}
            ambient_response = client.post("/api/ambient", json=ambient_request)
            assert ambient_response.status_code == 200
            
            # 3. Generate contextual ambient sound
            contextual_response = client.post(
                "/api/ambient/contextual",
                params={"object_type": "forest", "conversation_active": True}
            )
            assert contextual_response.status_code == 200
            
            # Verify all responses are successful
            assert types_response.json()["success"] is True
            assert ambient_response.json()["success"] is True
            assert contextual_response.json()["success"] is True
    
    def test_volume_mixing_property_validation(self, client, mock_ambient_audio):
        """Test that volume mixing property is consistently applied."""
        with patch('src.services.elevenlabs_service.ElevenLabsService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value.__aenter__.return_value = mock_service
            mock_service.generate_sound_effects.return_value = mock_ambient_audio
            mock_service._get_sound_description_for_object.return_value = {
                "primary_description": "Test sounds",
                "mood": "neutral",
                "secondary_sounds": []
            }
            mock_service.create_contextual_ambient_mix.return_value = mock_ambient_audio
            
            # Test basic ambient endpoint
            ambient_response = client.post("/api/ambient", json={"object_type": "test"})
            ambient_data = ambient_response.json()["data"]
            assert ambient_data["volume_mixed"] is True
            assert ambient_data["conversation_ready"] is True
            
            # Test contextual ambient endpoint
            contextual_response = client.post(
                "/api/ambient/contextual",
                params={"object_type": "test", "conversation_active": True}
            )
            contextual_data = contextual_response.json()["data"]
            assert contextual_data["volume_mixed"] is True
            assert contextual_data["speech_compatible"] is True