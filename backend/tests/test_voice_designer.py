"""
Tests for Voice Designer service.

Tests the Voice Design API integration functionality including
voice generation, style mapping, and session management.
"""
import pytest
from unittest.mock import AsyncMock, patch
import uuid

from src.services.voice_designer import VoiceDesigner
from src.models import ObjectProfile, VoiceStyle, VoiceConfig
from src.exceptions import ElevenLabsError


@pytest.fixture
def sample_profile():
    """Create a sample object profile for testing."""
    return ObjectProfile(
        id="test-profile-001",
        name="Whiskers",
        species="Tabby Cat",
        emoji="🐱",
        traits=["Curious", "Playful", "Wise"],
        backstory="A mysterious tabby cat who has lived in the old library for years."
    )


@pytest.fixture
def voice_designer():
    """Create VoiceDesigner instance for testing."""
    return VoiceDesigner(api_key="test-api-key")


class TestVoiceDesigner:
    """Test cases for VoiceDesigner class."""
    
    def test_init(self, voice_designer):
        """Test VoiceDesigner initialization."""
        assert voice_designer is not None
        assert len(voice_designer.style_configurations) == 6
        assert all(style in voice_designer.style_configurations for style in VoiceStyle)
        assert len(voice_designer.voice_sessions) == 0
    
    def test_get_voice_options(self, voice_designer):
        """Test getting voice style options."""
        options = voice_designer.get_voice_options()
        
        assert len(options) == 6
        assert all("style" in option for option in options)
        assert all("name" in option for option in options)
        assert all("description" in option for option in options)
        
        # Check all expected styles are present
        style_names = [option["style"] for option in options]
        expected_styles = [style.value for style in VoiceStyle]
        assert set(style_names) == set(expected_styles)
    
    def test_map_traits_to_voice_characteristics(self, voice_designer, sample_profile):
        """Test personality trait mapping to voice characteristics."""
        characteristics = voice_designer._map_traits_to_voice_characteristics(sample_profile.traits)
        
        assert len(characteristics) <= 3
        assert all(isinstance(char, str) for char in characteristics)
        assert len(characteristics) > 0
    
    def test_build_voice_description(self, voice_designer, sample_profile):
        """Test voice description generation."""
        description = voice_designer._build_voice_description(sample_profile, VoiceStyle.MYSTERIOUS)
        
        assert sample_profile.name in description
        assert sample_profile.species.lower() in description
        assert "mysterious" in description.lower()
        assert len(description) > 50  # Should be a substantial description
    
    def test_recommend_voice_style(self, voice_designer, sample_profile):
        """Test voice style recommendation."""
        recommended_style = voice_designer.recommend_voice_style(sample_profile)
        
        assert isinstance(recommended_style, VoiceStyle)
        # Should recommend a style that matches the traits
        assert recommended_style in VoiceStyle
    
    def test_recommend_voice_style_for_different_profiles(self, voice_designer):
        """Test voice style recommendations for different object types."""
        # Test mysterious object
        mysterious_profile = ObjectProfile(
            id="test-002",
            name="Shadow",
            species="Ancient Book",
            emoji="📚",
            traits=["Mysterious", "Dark", "Secretive"],
            backstory="An ancient tome of forgotten knowledge."
        )
        
        recommended = voice_designer.recommend_voice_style(mysterious_profile)
        # Should likely recommend MYSTERIOUS or WISE
        assert recommended in [VoiceStyle.MYSTERIOUS, VoiceStyle.WISE]
        
        # Test playful object
        playful_profile = ObjectProfile(
            id="test-003",
            name="Bouncy",
            species="Rubber Ball",
            emoji="⚽",
            traits=["Playful", "Energetic", "Fun"],
            backstory="A bouncy ball that loves to play games."
        )
        
        recommended = voice_designer.recommend_voice_style(playful_profile)
        # Should likely recommend PLAYFUL
        assert recommended == VoiceStyle.PLAYFUL
    
    def test_generate_profile_hash(self, voice_designer, sample_profile):
        """Test profile hash generation for caching."""
        hash1 = voice_designer._generate_profile_hash(sample_profile, VoiceStyle.MYSTERIOUS)
        hash2 = voice_designer._generate_profile_hash(sample_profile, VoiceStyle.MYSTERIOUS)
        hash3 = voice_designer._generate_profile_hash(sample_profile, VoiceStyle.PLAYFUL)
        
        # Same profile and style should generate same hash
        assert hash1 == hash2
        # Different style should generate different hash
        assert hash1 != hash3
        
        assert isinstance(hash1, str)
        assert len(hash1) > 0
    
    def test_voice_session_management(self, voice_designer):
        """Test voice configuration session storage and retrieval."""
        session_id = "test-session-001"
        voice_config = VoiceConfig(
            voice_id="test-voice-123",
            style=VoiceStyle.WARM,
            settings={"stability": 0.5, "similarity_boost": 0.7}
        )
        
        # Initially no config
        assert voice_designer.get_voice_config(session_id) is None
        
        # Store config
        voice_designer.store_voice_config(session_id, voice_config)
        assert voice_designer.get_session_count() == 1
        
        # Retrieve config
        retrieved_config = voice_designer.get_voice_config(session_id)
        assert retrieved_config is not None
        assert retrieved_config.voice_id == voice_config.voice_id
        assert retrieved_config.style == voice_config.style
        
        # Clear session
        cleared = voice_designer.clear_voice_session(session_id)
        assert cleared is True
        assert voice_designer.get_session_count() == 0
        assert voice_designer.get_voice_config(session_id) is None
        
        # Clear non-existent session
        cleared = voice_designer.clear_voice_session("non-existent")
        assert cleared is False
    
    @pytest.mark.asyncio
    async def test_create_voice_success(self, voice_designer, sample_profile):
        """Test successful voice creation."""
        mock_response = {"voice_id": "generated-voice-123"}
        
        with patch.object(voice_designer.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            voice_config = await voice_designer.create_voice(sample_profile, VoiceStyle.MYSTERIOUS)
            
            assert voice_config.voice_id == "generated-voice-123"
            assert voice_config.style == VoiceStyle.MYSTERIOUS
            assert "stability" in voice_config.settings
            
            # Verify API was called with correct parameters
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert "/voice-generation/generate-voice" in call_args[0]
            
            payload = call_args[1]["json_data"]
            assert "text" in payload
            assert "voice_description" in payload
            assert sample_profile.name in payload["text"]
    
    @pytest.mark.asyncio
    async def test_create_voice_with_caching(self, voice_designer, sample_profile):
        """Test voice creation with caching mechanism."""
        mock_response = {"voice_id": "cached-voice-456"}
        
        with patch.object(voice_designer.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            # First call should hit the API
            voice_config1 = await voice_designer.create_voice(sample_profile, VoiceStyle.WARM)
            assert mock_post.call_count == 1
            
            # Second call with same profile and style should use cache
            voice_config2 = await voice_designer.create_voice(sample_profile, VoiceStyle.WARM)
            assert mock_post.call_count == 1  # No additional API call
            
            # Both should return same voice ID
            assert voice_config1.voice_id == voice_config2.voice_id
    
    @pytest.mark.asyncio
    async def test_create_voice_api_error(self, voice_designer, sample_profile):
        """Test voice creation with API error."""
        with patch.object(voice_designer.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = Exception("API Error")
            
            with pytest.raises(ElevenLabsError) as exc_info:
                await voice_designer.create_voice(sample_profile, VoiceStyle.DRAMATIC)
            
            assert "Voice generation failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_create_voice_missing_voice_id(self, voice_designer, sample_profile):
        """Test voice creation with missing voice_id in response."""
        mock_response = {"status": "success"}  # Missing voice_id
        
        with patch.object(voice_designer.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            with pytest.raises(ElevenLabsError) as exc_info:
                await voice_designer.create_voice(sample_profile, VoiceStyle.WHISPERY)
            
            assert "Voice generation response missing voice_id" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(self, voice_designer):
        """Test cleanup of expired sessions (placeholder implementation)."""
        cleaned_count = await voice_designer.cleanup_expired_sessions()
        assert cleaned_count == 0  # Current implementation returns 0
    
    def test_style_configurations_completeness(self, voice_designer):
        """Test that all voice styles have complete configurations."""
        for style in VoiceStyle:
            config = voice_designer.style_configurations[style]
            
            # Check required fields
            assert "description_template" in config
            assert "personality_keywords" in config
            assert "voice_settings" in config
            assert "recommended_for" in config
            
            # Check voice settings structure
            settings = config["voice_settings"]
            assert "stability" in settings
            assert "similarity_boost" in settings
            assert "style" in settings
            
            # Check value ranges
            assert 0.0 <= settings["stability"] <= 1.0
            assert 0.0 <= settings["similarity_boost"] <= 1.0
            assert 0.0 <= settings["style"] <= 1.0
    
    @pytest.mark.asyncio
    async def test_context_manager(self, voice_designer):
        """Test async context manager functionality."""
        with patch.object(voice_designer.client, '__aenter__', new_callable=AsyncMock) as mock_enter:
            with patch.object(voice_designer.client, '__aexit__', new_callable=AsyncMock) as mock_exit:
                mock_enter.return_value = voice_designer.client
                
                async with voice_designer as designer:
                    assert designer is voice_designer
                
                mock_enter.assert_called_once()
                mock_exit.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])