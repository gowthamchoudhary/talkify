"""
Tests for Pydantic models and validation in VoiceSnap API.
"""
import pytest
from pydantic import ValidationError
from src.models import (
    VoiceStyle,
    ObjectIdentification,
    VoiceConfig,
    ObjectProfile,
    ConversationMessage,
    ConversationResponse,
    Song,
    APIResponse,
    ErrorResponse,
    ProfileRequest,
    SpeakRequest,
    SingRequest,
    AmbientRequest
)


class TestVoiceStyle:
    """Test VoiceStyle enum validation."""
    
    def test_valid_voice_styles(self):
        """Test all valid voice styles are accepted."""
        valid_styles = ["mysterious", "warm", "wise", "playful", "dramatic", "whispery"]
        for style in valid_styles:
            assert VoiceStyle(style) == style
    
    def test_invalid_voice_style(self):
        """Test invalid voice style raises ValueError."""
        with pytest.raises(ValueError):
            VoiceStyle("invalid_style")


class TestObjectIdentification:
    """Test ObjectIdentification model validation."""
    
    def test_valid_object_identification(self):
        """Test valid object identification creation."""
        data = {
            "object_type": "cat",
            "species": "domestic cat",
            "characteristics": ["fluffy", "orange", "playful"],
            "confidence": 0.95
        }
        obj = ObjectIdentification(**data)
        assert obj.object_type == "cat"
        assert obj.species == "domestic cat"
        assert len(obj.characteristics) == 3
        assert obj.confidence == 0.95
    
    def test_confidence_validation(self):
        """Test confidence score must be between 0 and 1."""
        # Valid confidence
        ObjectIdentification(
            object_type="cat",
            characteristics=["fluffy"],
            confidence=0.5
        )
        
        # Invalid confidence - too low
        with pytest.raises(ValidationError):
            ObjectIdentification(
                object_type="cat",
                characteristics=["fluffy"],
                confidence=-0.1
            )
        
        # Invalid confidence - too high
        with pytest.raises(ValidationError):
            ObjectIdentification(
                object_type="cat",
                characteristics=["fluffy"],
                confidence=1.1
            )
    
    def test_optional_species(self):
        """Test species field is optional."""
        obj = ObjectIdentification(
            object_type="rock",
            characteristics=["smooth", "gray"],
            confidence=0.8
        )
        assert obj.species is None


class TestVoiceConfig:
    """Test VoiceConfig model validation."""
    
    def test_valid_voice_config(self):
        """Test valid voice configuration creation."""
        config = VoiceConfig(
            voice_id="voice_123",
            style=VoiceStyle.WARM,
            settings={"stability": 0.7, "similarity_boost": 0.6, "style": 0.2}
        )
        assert config.voice_id == "voice_123"
        assert config.style == VoiceStyle.WARM
        assert config.settings["stability"] == 0.7
    
    def test_default_settings(self):
        """Test default voice settings are applied."""
        config = VoiceConfig(
            voice_id="voice_123",
            style=VoiceStyle.MYSTERIOUS
        )
        assert "stability" in config.settings
        assert "similarity_boost" in config.settings
        assert "style" in config.settings
        assert config.settings["stability"] == 0.5


class TestObjectProfile:
    """Test ObjectProfile model validation."""
    
    def test_valid_object_profile(self):
        """Test valid object profile creation."""
        profile = ObjectProfile(
            id="profile_123",
            name="Whiskers",
            species="cat",
            emoji="🐱",
            traits=["playful", "curious", "friendly"],
            backstory="A curious cat who loves to explore."
        )
        assert profile.name == "Whiskers"
        assert len(profile.traits) == 3
    
    def test_traits_validation(self):
        """Test exactly 3 traits are required."""
        # Too few traits
        with pytest.raises(ValidationError):
            ObjectProfile(
                id="profile_123",
                name="Whiskers",
                species="cat",
                emoji="🐱",
                traits=["playful", "curious"],  # Only 2 traits
                backstory="A curious cat."
            )
        
        # Too many traits
        with pytest.raises(ValidationError):
            ObjectProfile(
                id="profile_123",
                name="Whiskers",
                species="cat",
                emoji="🐱",
                traits=["playful", "curious", "friendly", "lazy"],  # 4 traits
                backstory="A curious cat."
            )
    
    def test_optional_voice_config(self):
        """Test voice_config is optional."""
        profile = ObjectProfile(
            id="profile_123",
            name="Whiskers",
            species="cat",
            emoji="🐱",
            traits=["playful", "curious", "friendly"],
            backstory="A curious cat."
        )
        assert profile.voice_config is None


class TestSong:
    """Test Song model validation."""
    
    def test_valid_song(self):
        """Test valid song creation."""
        song = Song(
            id="song_123",
            title="Cat's Melody",
            lyrics="Meow meow meow, I'm a happy cat",
            audio_url="https://example.com/song.mp3",
            duration=45.5
        )
        assert song.duration == 45.5
    
    def test_duration_constraints(self):
        """Test song duration must be between 30-90 seconds."""
        # Valid duration
        Song(
            id="song_123",
            title="Test Song",
            lyrics="Test lyrics",
            audio_url="https://example.com/song.mp3",
            duration=60.0
        )
        
        # Duration too short
        with pytest.raises(ValidationError):
            Song(
                id="song_123",
                title="Test Song",
                lyrics="Test lyrics",
                audio_url="https://example.com/song.mp3",
                duration=25.0  # Less than 30 seconds
            )
        
        # Duration too long
        with pytest.raises(ValidationError):
            Song(
                id="song_123",
                title="Test Song",
                lyrics="Test lyrics",
                audio_url="https://example.com/song.mp3",
                duration=95.0  # More than 90 seconds
            )


class TestConversationResponse:
    """Test ConversationResponse model validation."""
    
    def test_valid_conversation_response(self):
        """Test valid conversation response creation."""
        response = ConversationResponse(
            text="Hello there!",
            audio_url="https://example.com/response.mp3",
            session_id="session_123"
        )
        assert response.text == "Hello there!"
        assert response.session_id == "session_123"
        assert response.timestamp > 0


class TestAPIResponse:
    """Test APIResponse model validation."""
    
    def test_success_response(self):
        """Test successful API response."""
        response = APIResponse(
            success=True,
            data={"message": "Success"}
        )
        assert response.success is True
        assert response.data["message"] == "Success"
        assert response.error is None
        assert response.timestamp > 0
    
    def test_error_response(self):
        """Test error API response."""
        response = APIResponse(
            success=False,
            error={"code": "VALIDATION_ERROR", "message": "Invalid input"}
        )
        assert response.success is False
        assert response.error["code"] == "VALIDATION_ERROR"
        assert response.data is None


class TestRequestModels:
    """Test request model validation."""
    
    def test_profile_request(self):
        """Test ProfileRequest validation."""
        identification = ObjectIdentification(
            object_type="cat",
            characteristics=["fluffy"],
            confidence=0.9
        )
        request = ProfileRequest(
            identification=identification,
            voice_style=VoiceStyle.WARM
        )
        assert request.voice_style == VoiceStyle.WARM
    
    def test_speak_request(self):
        """Test SpeakRequest validation."""
        voice_config = VoiceConfig(
            voice_id="voice_123",
            style=VoiceStyle.PLAYFUL
        )
        request = SpeakRequest(
            text="Hello world!",
            voice_config=voice_config
        )
        assert request.text == "Hello world!"
        
        # Test text length limit
        with pytest.raises(ValidationError):
            SpeakRequest(
                text="x" * 1001,  # Exceeds 1000 character limit
                voice_config=voice_config
            )
    
    def test_ambient_request(self):
        """Test AmbientRequest validation."""
        request = AmbientRequest(
            object_type="forest",
            intensity=0.5
        )
        assert request.intensity == 0.5
        
        # Test intensity bounds
        with pytest.raises(ValidationError):
            AmbientRequest(
                object_type="forest",
                intensity=1.5  # Exceeds 1.0 limit
            )
        
        with pytest.raises(ValidationError):
            AmbientRequest(
                object_type="forest",
                intensity=-0.1  # Below 0.0 limit
            )


class TestBusinessConstraints:
    """Test business logic constraints across models."""
    
    def test_voice_style_consistency(self):
        """Test voice style consistency across models."""
        # Create voice config with specific style
        voice_config = VoiceConfig(
            voice_id="voice_123",
            style=VoiceStyle.DRAMATIC
        )
        
        # Create profile with same voice config
        profile = ObjectProfile(
            id="profile_123",
            name="Shakespeare",
            species="statue",
            emoji="🗿",
            traits=["dramatic", "eloquent", "theatrical"],
            backstory="A statue that speaks in dramatic verse.",
            voice_config=voice_config
        )
        
        assert profile.voice_config.style == VoiceStyle.DRAMATIC
    
    def test_complete_profile_generation(self):
        """Test that ObjectProfile contains all required fields for complete generation."""
        profile = ObjectProfile(
            id="profile_123",
            name="Buddy",
            species="dog",
            emoji="🐕",
            traits=["loyal", "energetic", "friendly"],
            backstory="A loyal companion who loves to play fetch."
        )
        
        # Verify all required fields are present and non-empty
        assert profile.id
        assert profile.name
        assert profile.species
        assert profile.emoji
        assert len(profile.traits) == 3
        assert all(trait for trait in profile.traits)  # No empty traits
        assert profile.backstory


class TestEnhancedValidation:
    """Test enhanced validation features."""
    
    def test_voice_config_settings_validation(self):
        """Test voice configuration settings validation."""
        # Valid settings
        VoiceConfig(
            voice_id="voice_123",
            style=VoiceStyle.WARM,
            settings={
                "stability": 0.7,
                "similarity_boost": 0.8,
                "style": 0.3
            }
        )
        
        # Invalid stability
        with pytest.raises(ValidationError):
            VoiceConfig(
                voice_id="voice_123",
                style=VoiceStyle.WARM,
                settings={"stability": 1.5}
            )
        
        # Invalid similarity_boost
        with pytest.raises(ValidationError):
            VoiceConfig(
                voice_id="voice_123",
                style=VoiceStyle.WARM,
                settings={"similarity_boost": -0.1}
            )
    
    def test_object_profile_enhanced_validation(self):
        """Test enhanced ObjectProfile validation."""
        # Valid profile
        ObjectProfile(
            id="profile_123",
            name="Buddy",
            species="dog",
            emoji="🐕",
            traits=["loyal", "energetic", "friendly"],
            backstory="A loyal companion who loves adventures."
        )
        
        # Empty name
        with pytest.raises(ValidationError):
            ObjectProfile(
                id="profile_123",
                name="   ",  # Just whitespace
                species="dog",
                emoji="🐕",
                traits=["loyal", "energetic", "friendly"],
                backstory="A loyal companion."
            )
        
        # Empty trait
        with pytest.raises(ValidationError):
            ObjectProfile(
                id="profile_123",
                name="Buddy",
                species="dog",
                emoji="🐕",
                traits=["loyal", "", "friendly"],  # Empty trait
                backstory="A loyal companion."
            )
        
        # Short backstory
        with pytest.raises(ValidationError):
            ObjectProfile(
                id="profile_123",
                name="Buddy",
                species="dog",
                emoji="🐕",
                traits=["loyal", "energetic", "friendly"],
                backstory="Short"  # Less than 10 characters
            )
    
    def test_song_enhanced_validation(self):
        """Test enhanced Song validation."""
        # Valid song
        Song(
            id="song_123",
            title="Happy Song",
            lyrics="La la la, I'm so happy today",
            audio_url="https://example.com/song.mp3",
            duration=45.0
        )
        
        # Empty title
        with pytest.raises(ValidationError):
            Song(
                id="song_123",
                title="   ",  # Just whitespace
                lyrics="La la la",
                audio_url="https://example.com/song.mp3",
                duration=45.0
            )
        
        # Empty lyrics
        with pytest.raises(ValidationError):
            Song(
                id="song_123",
                title="Happy Song",
                lyrics="",  # Empty lyrics
                audio_url="https://example.com/song.mp3",
                duration=45.0
            )
    
    def test_speak_request_enhanced_validation(self):
        """Test enhanced SpeakRequest validation."""
        voice_config = VoiceConfig(
            voice_id="voice_123",
            style=VoiceStyle.WARM
        )
        
        # Valid request
        SpeakRequest(
            text="Hello world!",
            voice_config=voice_config
        )
        
        # Empty text
        with pytest.raises(ValidationError):
            SpeakRequest(
                text="   ",  # Just whitespace
                voice_config=voice_config
            )
        
        # Text too short (empty after strip)
        with pytest.raises(ValidationError):
            SpeakRequest(
                text="",
                voice_config=voice_config
            )


class TestBusinessLogicValidation:
    """Test business logic validation across the system."""
    
    def test_complete_workflow_validation(self):
        """Test validation across a complete workflow."""
        # 1. Object identification
        identification = ObjectIdentification(
            object_type="cat",
            species="domestic cat",
            characteristics=["fluffy", "orange", "playful"],
            confidence=0.95
        )
        
        # 2. Profile generation
        profile = ObjectProfile(
            id="profile_123",
            name="Whiskers",
            species="cat",
            emoji="🐱",
            traits=["playful", "curious", "friendly"],
            backstory="A curious orange cat who loves to explore the neighborhood."
        )
        
        # 3. Voice configuration
        voice_config = VoiceConfig(
            voice_id="voice_cat_123",
            style=VoiceStyle.PLAYFUL,
            settings={
                "stability": 0.6,
                "similarity_boost": 0.7,
                "style": 0.4
            }
        )
        
        # 4. Add voice to profile
        profile.voice_config = voice_config
        
        # 5. Create speak request
        speak_request = SpeakRequest(
            text="Meow! Hello there, I'm Whiskers!",
            voice_config=voice_config
        )
        
        # 6. Create song
        song = Song(
            id="song_whiskers_123",
            title="Whiskers' Meow Song",
            lyrics="Meow meow meow, I'm a happy cat, Playing all day, imagine that!",
            audio_url="https://example.com/whiskers_song.mp3",
            duration=42.5
        )
        
        # Verify all objects are valid
        assert identification.confidence == 0.95
        assert len(profile.traits) == 3
        assert profile.voice_config.style == VoiceStyle.PLAYFUL
        assert 30.0 <= song.duration <= 90.0
        assert speak_request.text.strip()
    
    def test_error_response_structure(self):
        """Test error response structure validation."""
        # Success response
        success_response = APIResponse(
            success=True,
            data={"profile_id": "123", "name": "Whiskers"}
        )
        assert success_response.success is True
        assert success_response.error is None
        
        # Error response
        error_response = APIResponse(
            success=False,
            error={"code": "VALIDATION_ERROR", "message": "Invalid input"}
        )
        assert error_response.success is False
        assert error_response.data is None
        assert error_response.error["code"] == "VALIDATION_ERROR"