"""
Integration tests for Voice Designer functionality.

Simple tests that verify the Voice Designer works correctly without
complex mocking of async context managers.
"""
import pytest
from unittest.mock import patch, MagicMock

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


class TestVoiceDesignerIntegration:
    """Integration tests for Voice Designer functionality."""
    
    def test_voice_designer_initialization(self):
        """Test that VoiceDesigner initializes correctly."""
        designer = VoiceDesigner(api_key="test-key")
        
        assert designer is not None
        assert len(designer.style_configurations) == 6
        assert all(style in designer.style_configurations for style in VoiceStyle)
        assert len(designer.voice_sessions) == 0
        assert len(designer.voice_cache) == 0
    
    def test_get_voice_options_structure(self):
        """Test that voice options have correct structure."""
        designer = VoiceDesigner(api_key="test-key")
        options = designer.get_voice_options()
        
        assert len(options) == 6
        
        for option in options:
            assert "style" in option
            assert "name" in option
            assert "description" in option
            assert "keywords" in option
            assert "recommended_for" in option
            assert "settings" in option
            
            # Verify settings structure
            settings = option["settings"]
            assert "stability" in settings
            assert "similarity_boost" in settings
            assert "style" in settings
            
            # Verify value ranges
            assert 0.0 <= settings["stability"] <= 1.0
            assert 0.0 <= settings["similarity_boost"] <= 1.0
            assert 0.0 <= settings["style"] <= 1.0
    
    def test_voice_style_recommendation_logic(self, sample_profile):
        """Test voice style recommendation without API calls."""
        designer = VoiceDesigner(api_key="test-key")
        
        # Test with different profile types
        profiles = [
            ObjectProfile(
                id="mysterious-001",
                name="Shadow",
                species="Ancient Book",
                emoji="📚",
                traits=["Mysterious", "Dark", "Secretive"],
                backstory="An ancient tome of forgotten knowledge."
            ),
            ObjectProfile(
                id="playful-001",
                name="Bouncy",
                species="Rubber Ball",
                emoji="⚽",
                traits=["Playful", "Energetic", "Fun"],
                backstory="A bouncy ball that loves to play games."
            ),
            ObjectProfile(
                id="wise-001",
                name="Sage",
                species="Old Oak Tree",
                emoji="🌳",
                traits=["Wise", "Patient", "Ancient"],
                backstory="An old oak tree that has seen centuries pass."
            )
        ]
        
        for profile in profiles:
            recommended_style = designer.recommend_voice_style(profile)
            assert isinstance(recommended_style, VoiceStyle)
            
            # Verify recommendation makes sense based on traits
            if "mysterious" in [trait.lower() for trait in profile.traits]:
                assert recommended_style in [VoiceStyle.MYSTERIOUS, VoiceStyle.WISE]
            elif "playful" in [trait.lower() for trait in profile.traits]:
                assert recommended_style == VoiceStyle.PLAYFUL
            elif "wise" in [trait.lower() for trait in profile.traits]:
                assert recommended_style == VoiceStyle.WISE
    
    def test_voice_description_generation(self, sample_profile):
        """Test voice description generation logic."""
        designer = VoiceDesigner(api_key="test-key")
        
        for style in VoiceStyle:
            description = designer._build_voice_description(sample_profile, style)
            
            assert isinstance(description, str)
            assert len(description) > 50  # Should be substantial
            assert sample_profile.name in description
            assert sample_profile.species.lower() in description
            assert style.value in description.lower() or any(
                keyword in description.lower() 
                for keyword in designer.style_configurations[style]["personality_keywords"]
            )
    
    def test_trait_mapping_functionality(self):
        """Test personality trait to voice characteristic mapping."""
        designer = VoiceDesigner(api_key="test-key")
        
        test_cases = [
            (["Curious", "Friendly", "Wise"], 3),
            (["Mysterious"], 1),
            (["Playful", "Energetic", "Fun", "Cheerful"], 3),  # Should limit to 3
            (["Unknown", "Trait"], 2),  # Should handle unknown traits
        ]
        
        for traits, expected_count in test_cases:
            characteristics = designer._map_traits_to_voice_characteristics(traits)
            assert len(characteristics) <= expected_count
            assert all(isinstance(char, str) for char in characteristics)
            assert all(len(char) > 0 for char in characteristics)
    
    def test_session_management_functionality(self):
        """Test voice configuration session management."""
        designer = VoiceDesigner(api_key="test-key")
        
        # Create test voice configs
        voice_configs = [
            VoiceConfig(
                voice_id="voice-001",
                style=VoiceStyle.MYSTERIOUS,
                settings={"stability": 0.75, "similarity_boost": 0.65}
            ),
            VoiceConfig(
                voice_id="voice-002",
                style=VoiceStyle.PLAYFUL,
                settings={"stability": 0.45, "similarity_boost": 0.85}
            )
        ]
        
        session_ids = ["session-001", "session-002"]
        
        # Test storing configurations
        for session_id, voice_config in zip(session_ids, voice_configs):
            designer.store_voice_config(session_id, voice_config)
            assert designer.get_session_count() == len([s for s in session_ids if session_ids.index(s) <= session_ids.index(session_id)])
        
        # Test retrieving configurations
        for session_id, expected_config in zip(session_ids, voice_configs):
            retrieved_config = designer.get_voice_config(session_id)
            assert retrieved_config is not None
            assert retrieved_config.voice_id == expected_config.voice_id
            assert retrieved_config.style == expected_config.style
        
        # Test clearing sessions
        cleared = designer.clear_voice_session(session_ids[0])
        assert cleared is True
        assert designer.get_session_count() == 1
        assert designer.get_voice_config(session_ids[0]) is None
        assert designer.get_voice_config(session_ids[1]) is not None
        
        # Test clearing non-existent session
        cleared = designer.clear_voice_session("non-existent")
        assert cleared is False
    
    def test_profile_hash_generation_consistency(self, sample_profile):
        """Test that profile hashing is consistent and unique."""
        designer = VoiceDesigner(api_key="test-key")
        
        # Same profile and style should generate same hash
        hash1 = designer._generate_profile_hash(sample_profile, VoiceStyle.MYSTERIOUS)
        hash2 = designer._generate_profile_hash(sample_profile, VoiceStyle.MYSTERIOUS)
        assert hash1 == hash2
        
        # Different styles should generate different hashes
        hash3 = designer._generate_profile_hash(sample_profile, VoiceStyle.PLAYFUL)
        assert hash1 != hash3
        
        # Different profiles should generate different hashes
        different_profile = ObjectProfile(
            id="different-001",
            name="Different",
            species="Different Species",
            emoji="🔮",
            traits=["Different", "Traits", "Here"],
            backstory="A different backstory."
        )
        
        hash4 = designer._generate_profile_hash(different_profile, VoiceStyle.MYSTERIOUS)
        assert hash1 != hash4
    
    @pytest.mark.asyncio
    async def test_voice_creation_with_mocked_api(self, sample_profile):
        """Test voice creation with mocked ElevenLabs API."""
        designer = VoiceDesigner(api_key="test-key")
        
        # Mock the client's post method
        with patch.object(designer.client, 'post') as mock_post:
            mock_post.return_value = {"voice_id": "mocked-voice-123"}
            
            # Mock the client context manager
            with patch.object(designer.client, '__aenter__', return_value=designer.client):
                with patch.object(designer.client, '__aexit__', return_value=None):
                    
                    voice_config = await designer.create_voice(sample_profile, VoiceStyle.WARM)
                    
                    assert voice_config.voice_id == "mocked-voice-123"
                    assert voice_config.style == VoiceStyle.WARM
                    assert "stability" in voice_config.settings
                    
                    # Verify API was called
                    mock_post.assert_called_once()
                    call_args = mock_post.call_args
                    assert "/voice-generation/generate-voice" in call_args[0]
    
    @pytest.mark.asyncio
    async def test_voice_creation_caching(self, sample_profile):
        """Test that voice creation uses caching correctly."""
        designer = VoiceDesigner(api_key="test-key")
        
        with patch.object(designer.client, 'post') as mock_post:
            mock_post.return_value = {"voice_id": "cached-voice-456"}
            
            with patch.object(designer.client, '__aenter__', return_value=designer.client):
                with patch.object(designer.client, '__aexit__', return_value=None):
                    
                    # First call should hit the API
                    voice_config1 = await designer.create_voice(sample_profile, VoiceStyle.DRAMATIC)
                    assert mock_post.call_count == 1
                    
                    # Second call with same profile and style should use cache
                    voice_config2 = await designer.create_voice(sample_profile, VoiceStyle.DRAMATIC)
                    assert mock_post.call_count == 1  # No additional API call
                    
                    # Both should return same voice ID
                    assert voice_config1.voice_id == voice_config2.voice_id
    
    @pytest.mark.asyncio
    async def test_voice_creation_error_handling(self, sample_profile):
        """Test voice creation error handling."""
        designer = VoiceDesigner(api_key="test-key")
        
        with patch.object(designer.client, 'post') as mock_post:
            mock_post.side_effect = Exception("API Error")
            
            with patch.object(designer.client, '__aenter__', return_value=designer.client):
                with patch.object(designer.client, '__aexit__', return_value=None):
                    
                    with pytest.raises(ElevenLabsError) as exc_info:
                        await designer.create_voice(sample_profile, VoiceStyle.WHISPERY)
                    
                    assert "Voice generation failed" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__])