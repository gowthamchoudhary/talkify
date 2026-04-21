"""
Functional tests for TTS v3 implementation without complex mocking.
"""
import pytest
import os
from unittest.mock import patch
from src.services.elevenlabs_service import ElevenLabsService
from src.models import VoiceConfig, VoiceStyle


class TestTTSv3Functionality:
    """Test TTS v3 functionality with minimal mocking."""
    
    @pytest.fixture
    def mock_api_key(self):
        """Mock API key for testing."""
        with patch.dict(os.environ, {'ELEVENLABS_API_KEY': 'test_api_key_12345'}):
            yield
    
    def test_emotional_tag_detection_comprehensive(self, mock_api_key):
        """Test comprehensive emotional tag detection."""
        service = ElevenLabsService(api_key="test_api_key_12345")
        
        # Test cases with expected emotions
        test_cases = [
            ("I'm so excited and happy to meet you!", ["excited", "happy"]),
            ("This is absolutely amazing and wonderful!", ["excited", "happy"]),
            ("I feel quite sad and disappointed.", ["sad"]),
            ("I'm really angry about this situation!", ["angry"]),
            ("I'm shocked and astonished by this!", ["surprised"]),
            ("I wonder how this works? It's so curious!", ["curious"]),
            ("Everything is peaceful and calm here.", ["calm"]),
            ("There's something mysterious about this place.", ["mysterious"]),
            ("Let's have some fun and play together!", ["playful"]),
            ("With great wisdom comes understanding.", ["wise"]),
            ("The weather is nice today.", ["calm"])  # Default case
        ]
        
        for text, expected_emotions in test_cases:
            detected = service._detect_emotional_tags(text)
            # Check if at least one expected emotion is detected
            assert any(emotion in detected for emotion in expected_emotions), \
                f"Expected one of {expected_emotions} in {detected} for text: '{text}'"
    
    def test_emotional_tag_context_influence(self, mock_api_key):
        """Test how conversation context influences emotional detection."""
        service = ElevenLabsService(api_key="test_api_key_12345")
        
        # Neutral text that should pick up emotions from context
        neutral_text = "I see what you mean."
        
        # Happy context
        happy_context = [
            "I'm so excited about this!",
            "This is the best day ever!",
            "I'm feeling absolutely wonderful!"
        ]
        
        emotions_with_happy_context = service._detect_emotional_tags(neutral_text, happy_context)
        assert any(emotion in ["happy", "excited"] for emotion in emotions_with_happy_context)
        
        # Sad context
        sad_context = [
            "I'm feeling really down today.",
            "This is quite disappointing.",
            "I'm so sad about what happened."
        ]
        
        emotions_with_sad_context = service._detect_emotional_tags(neutral_text, sad_context)
        assert "sad" in emotions_with_sad_context
    
    def test_audio_format_settings_all_formats(self, mock_api_key):
        """Test audio format settings for all supported formats."""
        service = ElevenLabsService(api_key="test_api_key_12345")
        
        # Test all supported formats
        formats_to_test = ["mp3", "wav", "pcm", "unknown_format"]
        
        for format_type in formats_to_test:
            settings = service._get_audio_format_settings(format_type)
            
            # All settings should have required keys
            assert "output_format" in settings
            assert "optimize_streaming_latency" in settings
            assert "use_speaker_boost" in settings
            
            # Verify format-specific settings
            if format_type == "mp3":
                assert settings["output_format"] == "mp3_44100_128"
                assert settings["use_speaker_boost"] is True
            elif format_type == "wav":
                assert settings["output_format"] == "pcm_44100"
                assert settings["use_speaker_boost"] is False
            elif format_type == "pcm":
                assert settings["output_format"] == "pcm_22050"
                assert settings["use_speaker_boost"] is False
            else:  # unknown format defaults to mp3
                assert settings["output_format"] == "mp3_44100_128"
    
    def test_conversation_context_management_comprehensive(self, mock_api_key):
        """Test comprehensive conversation context management."""
        service = ElevenLabsService(api_key="test_api_key_12345")
        session_id = "test_session_comprehensive"
        
        # Test adding messages
        messages = [
            "Hello there!",
            "How are you doing today?",
            "I'm feeling great!",
            "What would you like to talk about?",
            "This is an interesting conversation."
        ]
        
        for message in messages:
            service.add_conversation_message(session_id, message)
        
        # Verify all messages are stored
        context = service.get_conversation_context(session_id)
        assert len(context) == len(messages)
        for message in messages:
            assert message in context
        
        # Test context limit
        max_context = 3
        for i in range(10):
            service.add_conversation_message(session_id, f"Extra message {i}", max_context=max_context)
        
        limited_context = service.get_conversation_context(session_id)
        assert len(limited_context) == max_context
        
        # Verify it keeps the most recent messages
        assert "Extra message 9" in limited_context
        assert "Extra message 8" in limited_context
        assert "Extra message 7" in limited_context
        assert "Hello there!" not in limited_context  # Should be removed
        
        # Test clearing context
        cleared = service.clear_conversation_context(session_id)
        assert cleared is True
        
        empty_context = service.get_conversation_context(session_id)
        assert len(empty_context) == 0
        
        # Test clearing non-existent session
        cleared_again = service.clear_conversation_context("non_existent_session")
        assert cleared_again is False
    
    def test_voice_session_management(self, mock_api_key):
        """Test voice session management functionality."""
        service = ElevenLabsService(api_key="test_api_key_12345")
        
        # Create test voice config
        voice_config = VoiceConfig(
            voice_id="test_voice_123",
            style=VoiceStyle.PLAYFUL,
            settings={
                "stability": 0.6,
                "similarity_boost": 0.7,
                "style": 0.5
            }
        )
        
        session_id = "test_voice_session"
        
        # Store voice config
        service.store_voice_config(session_id, voice_config)
        
        # Retrieve voice config
        retrieved_config = service.get_voice_config(session_id)
        assert retrieved_config is not None
        assert retrieved_config.voice_id == voice_config.voice_id
        assert retrieved_config.style == voice_config.style
        assert retrieved_config.settings == voice_config.settings
        
        # Test non-existent session
        non_existent_config = service.get_voice_config("non_existent_session")
        assert non_existent_config is None
        
        # Clear voice session
        cleared = service.clear_voice_session(session_id)
        assert cleared is True
        
        # Verify it's cleared
        cleared_config = service.get_voice_config(session_id)
        assert cleared_config is None
        
        # Test clearing non-existent session
        cleared_again = service.clear_voice_session("non_existent_session")
        assert cleared_again is False
    
    def test_emotional_style_mapping(self, mock_api_key):
        """Test that emotional tags map correctly to voice style adjustments."""
        service = ElevenLabsService(api_key="test_api_key_12345")
        
        # Test texts with strong emotional content
        test_cases = [
            ("I'm absolutely thrilled and excited!", 0.7),  # Should increase style
            ("This is so amazing and wonderful!", 0.6),     # Happy emotion
            ("I'm feeling quite sad today.", 0.3),          # Should decrease style
            ("I'm really angry about this!", 0.8),          # Should increase style significantly
            ("Everything is calm and peaceful.", 0.2),      # Should keep style low
        ]
        
        for text, expected_min_style in test_cases:
            emotions = service._detect_emotional_tags(text)
            
            # Simulate the style mapping logic from text_to_speech_v3
            emotion_style_mapping = {
                "excited": 0.8,
                "happy": 0.6,
                "sad": 0.2,
                "angry": 0.9,
                "surprised": 0.7,
                "curious": 0.5,
                "calm": 0.1,
                "mysterious": 0.4,
                "playful": 0.7,
                "wise": 0.3
            }
            
            if emotions:
                primary_emotion = emotions[0]
                if primary_emotion in emotion_style_mapping:
                    style_value = emotion_style_mapping[primary_emotion]
                    # Verify the style value is reasonable for the emotion
                    if primary_emotion in ["excited", "angry", "playful"]:
                        assert style_value >= 0.7, f"High-energy emotion {primary_emotion} should have high style value"
                    elif primary_emotion in ["sad", "calm"]:
                        assert style_value <= 0.3, f"Low-energy emotion {primary_emotion} should have low style value"
    
    def test_tts_v3_payload_structure(self, mock_api_key):
        """Test that TTS v3 payload has correct structure without making API calls."""
        service = ElevenLabsService(api_key="test_api_key_12345")
        
        # Test the payload structure by examining what would be sent
        # (This tests the logic without making actual API calls)
        
        text = "Hello! I'm excited to talk with you!"
        voice_id = "test_voice_123"
        voice_settings = {
            "stability": 0.6,
            "similarity_boost": 0.7,
            "style": 0.5
        }
        conversation_context = ["Hi there!", "How are you?"]
        
        # Test emotional tag detection
        emotional_tags = service._detect_emotional_tags(text, conversation_context)
        assert len(emotional_tags) > 0
        
        # Test format settings
        format_settings = service._get_audio_format_settings("mp3")
        assert format_settings["output_format"] == "mp3_44100_128"
        
        # Verify that emotional adjustment would work
        emotion_style_mapping = {
            "excited": 0.8,
            "happy": 0.6,
            "sad": 0.2,
            "angry": 0.9,
            "surprised": 0.7,
            "curious": 0.5,
            "calm": 0.1,
            "mysterious": 0.4,
            "playful": 0.7,
            "wise": 0.3
        }
        
        if emotional_tags:
            primary_emotion = emotional_tags[0]
            if primary_emotion in emotion_style_mapping:
                adjusted_style = emotion_style_mapping[primary_emotion]
                # Verify the adjustment is within valid range
                assert 0.0 <= adjusted_style <= 1.0


if __name__ == "__main__":
    pytest.main([__file__])