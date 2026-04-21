"""
Tests for conversational AI integration in ElevenLabsService.

Tests the new conversation methods added for task 3.5:
- Real-time conversation processing
- Conversation context maintenance
- Session management
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import uuid
import time

from src.services.elevenlabs_service import ElevenLabsService
from src.models import ObjectProfile, VoiceConfig, VoiceStyle
from src.exceptions import ElevenLabsError


class TestConversationalAI:
    """Test conversational AI functionality."""
    
    @pytest.fixture
    def sample_profile(self):
        """Create a sample object profile for testing."""
        return ObjectProfile(
            id="test_profile_123",
            name="Whiskers",
            species="Cat",
            emoji="🐱",
            traits=["Curious", "Playful", "Wise"],
            backstory="A mysterious cat who loves to share stories and adventures."
        )
    
    @pytest.fixture
    def sample_voice_config(self):
        """Create a sample voice configuration for testing."""
        return VoiceConfig(
            voice_id="test_voice_123",
            style=VoiceStyle.MYSTERIOUS,
            settings={
                "stability": 0.7,
                "similarity_boost": 0.6,
                "style": 0.8
            }
        )
    
    @pytest.mark.asyncio
    async def test_start_conversation_session(self, sample_profile, sample_voice_config):
        """Test starting a new conversation session."""
        with patch('src.services.elevenlabs_service.ElevenLabsClient'):
            service = ElevenLabsService(api_key="test_api_key_12345")
            
            # Start conversation session
            session_id = await service.start_conversation_session(sample_profile, sample_voice_config)
            
            # Verify session ID is generated
            assert session_id is not None
            assert isinstance(session_id, str)
            assert len(session_id) > 0
            
            # Verify session is stored
            assert session_id in service.conversation_contexts
            assert session_id in service.voice_sessions
            
            # Verify initial context is set
            context = service.get_conversation_context(session_id)
            assert len(context) > 0
            assert sample_profile.name in " ".join(context)
            assert sample_profile.species in " ".join(context)
            
            # Verify voice config is stored
            stored_voice_config = service.get_voice_config(session_id)
            assert stored_voice_config is not None
            assert stored_voice_config.voice_id == sample_voice_config.voice_id
            assert stored_voice_config.style == sample_voice_config.style
    
    @pytest.mark.asyncio
    async def test_process_conversation_input(self, sample_profile, sample_voice_config):
        """Test processing conversation input with audio data."""
        with patch('src.services.elevenlabs_service.ElevenLabsClient'):
            service = ElevenLabsService(api_key="test_api_key_12345")
            
            # Mock the text_to_speech_v3 method
            mock_audio_data = b"fake_audio_response_data"
            service.text_to_speech_v3 = AsyncMock(return_value=mock_audio_data)
            
            # Start conversation session
            session_id = await service.start_conversation_session(sample_profile, sample_voice_config)
            
            # Process conversation input
            fake_audio_input = b"fake_user_audio_input"
            response = await service.process_conversation_input(
                session_id=session_id,
                audio_data=fake_audio_input,
                audio_format="mp3"
            )
            
            # Verify response structure
            assert isinstance(response, dict)
            assert "session_id" in response
            assert "response_text" in response
            assert "response_audio" in response
            assert "audio_format" in response
            assert "voice_id" in response
            assert "timestamp" in response
            
            # Verify response content
            assert response["session_id"] == session_id
            assert response["response_audio"] == mock_audio_data
            assert response["audio_format"] == "mp3"
            assert response["voice_id"] == sample_voice_config.voice_id
            assert isinstance(response["response_text"], str)
            assert len(response["response_text"]) > 0
            
            # Verify TTS was called
            service.text_to_speech_v3.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_conversation_input_no_session(self):
        """Test processing conversation input with invalid session ID."""
        with patch('src.services.elevenlabs_service.ElevenLabsClient'):
            service = ElevenLabsService(api_key="test_api_key_12345")
            
            # Try to process input for non-existent session
            with pytest.raises(ElevenLabsError) as exc_info:
                await service.process_conversation_input(
                    session_id="non_existent_session",
                    audio_data=b"fake_audio",
                    audio_format="mp3"
                )
            
            assert "No voice configuration found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_generate_contextual_response(self, sample_profile, sample_voice_config):
        """Test contextual response generation."""
        with patch('src.services.elevenlabs_service.ElevenLabsClient'):
            service = ElevenLabsService(api_key="test_api_key_12345")
            
            # Start conversation session
            session_id = await service.start_conversation_session(sample_profile, sample_voice_config)
            
            # Get initial context
            context = service.get_conversation_context(session_id)
            
            # Generate response
            response_text = await service._generate_contextual_response(session_id, context)
            
            # Verify response
            assert isinstance(response_text, str)
            assert len(response_text) > 0
            assert response_text.strip() != ""
            
            # Add more context and generate another response
            service.add_conversation_message(session_id, "User: Hello there!")
            service.add_conversation_message(session_id, "AI: Hello! Nice to meet you!")
            service.add_conversation_message(session_id, "User: How are you doing?")
            
            updated_context = service.get_conversation_context(session_id)
            response_text_2 = await service._generate_contextual_response(session_id, updated_context)
            
            # Verify second response
            assert isinstance(response_text_2, str)
            assert len(response_text_2) > 0
            
            # Responses should be consistent for same session (based on session ID hash)
            response_text_3 = await service._generate_contextual_response(session_id, updated_context)
            assert response_text_2 == response_text_3
    
    @pytest.mark.asyncio
    async def test_end_conversation_session(self, sample_profile, sample_voice_config):
        """Test ending a conversation session."""
        with patch('src.services.elevenlabs_service.ElevenLabsClient'):
            service = ElevenLabsService(api_key="test_api_key_12345")
            
            # Start conversation session
            session_id = await service.start_conversation_session(sample_profile, sample_voice_config)
            
            # Verify session exists
            assert session_id in service.conversation_contexts
            assert session_id in service.voice_sessions
            
            # End session
            result = await service.end_conversation_session(session_id)
            
            # Verify session was ended
            assert result is True
            assert session_id not in service.conversation_contexts
            assert session_id not in service.voice_sessions
            
            # Try to end non-existent session
            result_2 = await service.end_conversation_session("non_existent_session")
            assert result_2 is False
    
    @pytest.mark.asyncio
    async def test_get_conversation_status(self, sample_profile, sample_voice_config):
        """Test getting conversation session status."""
        with patch('src.services.elevenlabs_service.ElevenLabsClient'):
            service = ElevenLabsService(api_key="test_api_key_12345")
            
            # Get status for non-existent session
            status = await service.get_conversation_status("non_existent_session")
            assert status["active"] is False
            assert status["voice_configured"] is False
            assert status["voice_id"] is None
            assert status["context_messages"] == 0
            
            # Start conversation session
            session_id = await service.start_conversation_session(sample_profile, sample_voice_config)
            
            # Get status for active session
            status = await service.get_conversation_status(session_id)
            assert status["session_id"] == session_id
            assert status["active"] is True
            assert status["voice_configured"] is True
            assert status["voice_id"] == sample_voice_config.voice_id
            assert status["voice_style"] == sample_voice_config.style.value
            assert status["context_messages"] > 0
            assert status["last_activity"] is not None
            
            # Add some messages and check updated status
            service.add_conversation_message(session_id, "Test message 1")
            service.add_conversation_message(session_id, "Test message 2")
            
            updated_status = await service.get_conversation_status(session_id)
            assert updated_status["context_messages"] > status["context_messages"]
    
    @pytest.mark.asyncio
    async def test_conversation_context_preservation(self, sample_profile, sample_voice_config):
        """Test that conversation context is preserved throughout the session."""
        with patch('src.services.elevenlabs_service.ElevenLabsClient'):
            service = ElevenLabsService(api_key="test_api_key_12345")
            
            # Start conversation session
            session_id = await service.start_conversation_session(sample_profile, sample_voice_config)
            
            # Get initial context
            initial_context = service.get_conversation_context(session_id)
            initial_count = len(initial_context)
            
            # Add conversation messages
            messages = [
                "User: Hello, what's your name?",
                "AI: Hi! I'm Whiskers, nice to meet you!",
                "User: Tell me about yourself.",
                "AI: I'm a curious cat who loves adventures!",
                "User: What do you like to do?",
                "AI: I enjoy exploring and sharing stories."
            ]
            
            for message in messages:
                service.add_conversation_message(session_id, message)
            
            # Verify context preservation
            final_context = service.get_conversation_context(session_id)
            assert len(final_context) == initial_count + len(messages)
            
            # Verify all messages are preserved in order
            for message in messages:
                assert message in final_context
            
            # Verify context can be retrieved consistently
            context_copy = service.get_conversation_context(session_id)
            assert context_copy == final_context
            
            # Test context limit functionality
            service.add_conversation_message(session_id, "Extra message", max_context=5)
            limited_context = service.get_conversation_context(session_id)
            assert len(limited_context) <= 5
    
    def test_conversation_session_isolation(self):
        """Test that different conversation sessions are isolated from each other."""
        with patch('src.services.elevenlabs_service.ElevenLabsClient'):
            service = ElevenLabsService(api_key="test_api_key_12345")
            
            # Create two different sessions
            session_1 = "session_1"
            session_2 = "session_2"
            
            # Add different messages to each session
            service.add_conversation_message(session_1, "Session 1 message 1")
            service.add_conversation_message(session_1, "Session 1 message 2")
            
            service.add_conversation_message(session_2, "Session 2 message 1")
            service.add_conversation_message(session_2, "Session 2 message 2")
            service.add_conversation_message(session_2, "Session 2 message 3")
            
            # Verify sessions are isolated
            context_1 = service.get_conversation_context(session_1)
            context_2 = service.get_conversation_context(session_2)
            
            assert len(context_1) == 2
            assert len(context_2) == 3
            assert "Session 1" in " ".join(context_1)
            assert "Session 2" in " ".join(context_2)
            assert "Session 1" not in " ".join(context_2)
            assert "Session 2" not in " ".join(context_1)
            
            # Clear one session and verify the other is unaffected
            service.clear_conversation_context(session_1)
            
            assert len(service.get_conversation_context(session_1)) == 0
            assert len(service.get_conversation_context(session_2)) == 3