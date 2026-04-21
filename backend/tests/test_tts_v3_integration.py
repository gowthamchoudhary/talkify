"""
Tests for ElevenLabs TTS v3 API integration with emotional tags.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.services.elevenlabs_service import ElevenLabsService
from src.models import VoiceConfig, VoiceStyle
from src.exceptions import ElevenLabsError


class TestTTSv3Integration:
    """Test TTS v3 API integration functionality."""
    
    @pytest.fixture
    def mock_elevenlabs_client(self):
        """Mock ElevenLabs client for testing."""
        with patch('src.services.elevenlabs_service.ElevenLabsClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            yield mock_client
    
    @pytest.fixture
    def voice_config(self):
        """Sample voice configuration for testing."""
        return VoiceConfig(
            voice_id="test_voice_123",
            style=VoiceStyle.PLAYFUL,
            settings={
                "stability": 0.6,
                "similarity_boost": 0.7,
                "style": 0.5
            }
        )
    
    @pytest.mark.asyncio
    async def test_emotional_tag_detection(self, mock_elevenlabs_client):
        """Test emotional tag detection from text content."""
        service = ElevenLabsService()
        
        # Test excited emotion detection
        excited_text = "This is amazing! I'm so excited to meet you!"
        emotions = service._detect_emotional_tags(excited_text)
        assert "excited" in emotions or "happy" in emotions
        
        # Test sad emotion detection
        sad_text = "I'm feeling quite sad and disappointed today."
        emotions = service._detect_emotional_tags(sad_text)
        assert "sad" in emotions
        
        # Test curious emotion detection
        curious_text = "I wonder what that is? How does it work?"
        emotions = service._detect_emotional_tags(curious_text)
        assert "curious" in emotions
        
        # Test default emotion when none detected
        neutral_text = "The weather is nice today."
        emotions = service._detect_emotional_tags(neutral_text)
        assert "calm" in emotions
    
    @pytest.mark.asyncio
    async def test_emotional_tag_detection_with_context(self, mock_elevenlabs_client):
        """Test emotional tag detection with conversation context."""
        service = ElevenLabsService()
        
        # Context with emotional content
        context = [
            "I'm so happy to see you!",
            "This is wonderful!",
            "What an amazing day!"
        ]
        
        neutral_text = "Yes, I agree."
        emotions = service._detect_emotional_tags(neutral_text, context)
        
        # Should pick up happy emotions from context
        assert any(emotion in ["happy", "excited"] for emotion in emotions)
    
    @pytest.mark.asyncio
    async def test_audio_format_settings(self, mock_elevenlabs_client):
        """Test audio format settings for different formats."""
        service = ElevenLabsService()
        
        # Test MP3 format settings
        mp3_settings = service._get_audio_format_settings("mp3")
        assert mp3_settings["output_format"] == "mp3_44100_128"
        assert mp3_settings["use_speaker_boost"] is True
        
        # Test WAV format settings
        wav_settings = service._get_audio_format_settings("wav")
        assert wav_settings["output_format"] == "pcm_44100"
        assert wav_settings["use_speaker_boost"] is False
        
        # Test default format (should be MP3)
        default_settings = service._get_audio_format_settings("unknown")
        assert default_settings["output_format"] == "mp3_44100_128"
    
    @pytest.mark.asyncio
    async def test_text_to_speech_v3_success(self, mock_elevenlabs_client, voice_config):
        """Test successful TTS v3 conversion with emotional tags."""
        # Mock successful API response
        mock_audio_data = b"fake_audio_data_12345"
        mock_elevenlabs_client.post_audio.return_value = mock_audio_data
        
        service = ElevenLabsService()
        
        text = "Hello! I'm so excited to talk with you!"
        conversation_context = ["Hi there!", "How are you doing?"]
        
        result = await service.text_to_speech_v3(
            text=text,
            voice_id=voice_config.voice_id,
            voice_settings=voice_config.settings,
            conversation_context=conversation_context,
            audio_format="mp3",
            enable_streaming=True
        )
        
        # Verify the result
        assert result == mock_audio_data
        
        # Verify the API was called with correct parameters
        mock_elevenlabs_client.post_audio.assert_called_once()
        call_args = mock_elevenlabs_client.post_audio.call_args
        
        # Check endpoint
        assert call_args[0][0] == f"/text-to-speech/{voice_config.voice_id}/stream"
        
        # Check payload structure
        payload = call_args[1]["json_data"]
        assert payload["text"] == text
        assert payload["model_id"] == "eleven_turbo_v2_5"
        assert "voice_settings" in payload
        assert payload["response_format"] == "mp3_44100_128"
    
    @pytest.mark.asyncio
    async def test_text_to_speech_v3_with_emotional_adjustment(self, mock_elevenlabs_client, voice_config):
        """Test TTS v3 with emotional style adjustment."""
        mock_audio_data = b"emotional_audio_data"
        mock_elevenlabs_client.post_audio.return_value = mock_audio_data
        
        service = ElevenLabsService()
        
        # Text with strong emotional content
        excited_text = "This is absolutely amazing and wonderful!"
        
        result = await service.text_to_speech_v3(
            text=excited_text,
            voice_id=voice_config.voice_id,
            voice_settings=voice_config.settings
        )
        
        # Verify the call was made
        mock_elevenlabs_client.post_audio.assert_called_once()
        payload = mock_elevenlabs_client.post_audio.call_args[1]["json_data"]
        
        # Check that style was adjusted for emotion (should be higher than original 0.5)
        assert payload["voice_settings"]["style"] > 0.5
    
    @pytest.mark.asyncio
    async def test_text_to_speech_v3_error_handling(self, mock_elevenlabs_client, voice_config):
        """Test TTS v3 error handling."""
        # Mock API error
        mock_elevenlabs_client.post_audio.side_effect = Exception("API Error")
        
        service = ElevenLabsService()
        
        with pytest.raises(ElevenLabsError) as exc_info:
            await service.text_to_speech_v3(
                text="Test text",
                voice_id=voice_config.voice_id
            )
        
        assert "TTS v3 conversion failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_conversation_context_management(self, mock_elevenlabs_client):
        """Test conversation context management for emotional analysis."""
        service = ElevenLabsService()
        session_id = "test_session_123"
        
        # Add messages to context
        service.add_conversation_message(session_id, "Hello there!")
        service.add_conversation_message(session_id, "How are you doing?")
        service.add_conversation_message(session_id, "I'm feeling great!")
        
        # Get context
        context = service.get_conversation_context(session_id)
        assert len(context) == 3
        assert "Hello there!" in context
        assert "I'm feeling great!" in context
        
        # Test context limit (add more messages than max_context)
        for i in range(15):
            service.add_conversation_message(session_id, f"Message {i}", max_context=10)
        
        context = service.get_conversation_context(session_id)
        assert len(context) == 10  # Should be limited to max_context
        
        # Clear context
        cleared = service.clear_conversation_context(session_id)
        assert cleared is True
        
        context = service.get_conversation_context(session_id)
        assert len(context) == 0
    
    @pytest.mark.asyncio
    async def test_legacy_text_to_speech_compatibility(self, mock_elevenlabs_client, voice_config):
        """Test that legacy text_to_speech method still works."""
        mock_audio_data = b"legacy_audio_data"
        mock_elevenlabs_client.post_audio.return_value = mock_audio_data
        
        service = ElevenLabsService()
        
        result = await service.text_to_speech(
            text="Legacy test",
            voice_id=voice_config.voice_id,
            voice_settings=voice_config.settings
        )
        
        assert result == mock_audio_data
        mock_elevenlabs_client.post_audio.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_audio_streaming_preparation(self, mock_elevenlabs_client):
        """Test audio streaming preparation."""
        service = ElevenLabsService()
        
        test_audio_data = b"test_audio_stream_data"
        
        # Test streaming preparation
        streamed_data = await service.stream_audio_response(test_audio_data)
        assert streamed_data == test_audio_data  # Currently returns as-is
        
        # Test audio format conversion (placeholder)
        converted_data = await service.convert_audio_format(test_audio_data, "wav")
        assert converted_data == test_audio_data  # Currently returns as-is


if __name__ == "__main__":
    pytest.main([__file__])