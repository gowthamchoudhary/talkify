"""
Tests for WebSocket conversation handler.

Tests the WebSocket functionality for real-time conversation processing.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json
import time

from src.websocket_handler import ConversationWebSocketManager
from src.models import ObjectProfile, VoiceConfig, VoiceStyle


class TestWebSocketHandler:
    """Test WebSocket conversation handler functionality."""
    
    @pytest.fixture
    def websocket_manager(self):
        """Create a WebSocket manager for testing."""
        return ConversationWebSocketManager()
    
    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket for testing."""
        websocket = AsyncMock()
        websocket.client_state = "CONNECTED"
        return websocket
    
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
    async def test_websocket_connect(self, websocket_manager, mock_websocket, sample_profile, sample_voice_config):
        """Test WebSocket connection establishment."""
        session_id = "test_session_123"
        
        with patch('src.websocket_handler.ElevenLabsService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            
            # Test connection
            result = await websocket_manager.connect(
                websocket=mock_websocket,
                session_id=session_id,
                profile=sample_profile,
                voice_config=sample_voice_config
            )
            
            # Verify connection was successful
            assert result is True
            assert session_id in websocket_manager.active_connections
            assert session_id in websocket_manager.session_services
            assert session_id in websocket_manager.connection_metadata
            
            # Verify WebSocket was accepted
            mock_websocket.accept.assert_called_once()
            
            # Verify service was initialized
            mock_service.__aenter__.assert_called_once()
            mock_service.start_conversation_session.assert_called_once_with(sample_profile, sample_voice_config)
            
            # Verify connection confirmation was sent
            mock_websocket.send_text.assert_called()
    
    @pytest.mark.asyncio
    async def test_websocket_disconnect(self, websocket_manager, mock_websocket):
        """Test WebSocket disconnection and cleanup."""
        session_id = "test_session_123"
        
        with patch('src.websocket_handler.ElevenLabsService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            
            # Connect first
            await websocket_manager.connect(mock_websocket, session_id)
            
            # Verify connection exists
            assert session_id in websocket_manager.active_connections
            
            # Disconnect
            await websocket_manager.disconnect(session_id)
            
            # Verify cleanup
            assert session_id not in websocket_manager.active_connections
            assert session_id not in websocket_manager.session_services
            assert session_id not in websocket_manager.connection_metadata
            
            # Verify service cleanup
            mock_service.end_conversation_session.assert_called_once_with(session_id)
            mock_service.__aexit__.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_message(self, websocket_manager, mock_websocket):
        """Test sending messages through WebSocket."""
        session_id = "test_session_123"
        
        with patch('src.websocket_handler.ElevenLabsService'):
            # Connect first
            await websocket_manager.connect(mock_websocket, session_id)
            
            # Send message
            test_message = {"type": "test", "content": "Hello World"}
            result = await websocket_manager.send_message(session_id, test_message)
            
            # Verify message was sent
            assert result is True
            
            # Verify WebSocket send_text was called
            assert mock_websocket.send_text.call_count >= 2  # Connection confirmation + test message
            
            # Get the last call (our test message)
            last_call_args = mock_websocket.send_text.call_args_list[-1]
            sent_data = json.loads(last_call_args[0][0])
            
            assert sent_data["type"] == "test"
            assert sent_data["content"] == "Hello World"
            assert "timestamp" in sent_data
    
    @pytest.mark.asyncio
    async def test_send_audio(self, websocket_manager, mock_websocket):
        """Test sending audio data through WebSocket."""
        session_id = "test_session_123"
        
        with patch('src.websocket_handler.ElevenLabsService'):
            # Connect first
            await websocket_manager.connect(mock_websocket, session_id)
            
            # Send audio
            audio_data = b"fake_audio_data_12345"
            metadata = {"format": "mp3", "duration": 5.0}
            result = await websocket_manager.send_audio(session_id, audio_data, metadata)
            
            # Verify audio was sent
            assert result is True
            
            # Verify both text (metadata) and bytes (audio) were sent
            mock_websocket.send_text.assert_called()  # For metadata
            mock_websocket.send_bytes.assert_called_once_with(audio_data)
    
    @pytest.mark.asyncio
    async def test_handle_setup_conversation_message(self, websocket_manager, mock_websocket, sample_profile, sample_voice_config):
        """Test handling setup conversation message."""
        session_id = "test_session_123"
        
        with patch('src.websocket_handler.ElevenLabsService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            
            # Connect without profile/voice config
            await websocket_manager.connect(mock_websocket, session_id)
            
            # Send setup message
            setup_message = {
                "type": "setup_conversation",
                "profile": sample_profile.model_dump(),
                "voice_config": sample_voice_config.model_dump()
            }
            
            await websocket_manager.handle_message(session_id, setup_message)
            
            # Verify setup was processed
            mock_service.start_conversation_session.assert_called()
            
            # Verify metadata was updated
            metadata = websocket_manager.connection_metadata[session_id]
            assert metadata["profile"] is not None
            assert metadata["voice_config"] is not None
    
    @pytest.mark.asyncio
    async def test_handle_text_input_message(self, websocket_manager, mock_websocket, sample_profile, sample_voice_config):
        """Test handling text input message."""
        session_id = "test_session_123"
        
        with patch('src.websocket_handler.ElevenLabsService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            
            # Mock service methods
            mock_service._generate_contextual_response.return_value = "Hello! Nice to meet you!"
            mock_service.text_to_speech_v3.return_value = b"fake_audio_response"
            
            # Connect with profile and voice config
            await websocket_manager.connect(mock_websocket, session_id, sample_profile, sample_voice_config)
            
            # Send text input message
            text_message = {
                "type": "text_input",
                "text": "Hello there!"
            }
            
            await websocket_manager.handle_message(session_id, text_message)
            
            # Verify text processing
            mock_service.add_conversation_message.assert_called()
            mock_service._generate_contextual_response.assert_called_once()
            mock_service.text_to_speech_v3.assert_called_once()
            
            # Verify response was sent
            assert mock_websocket.send_text.call_count >= 2  # Connection + response
            assert mock_websocket.send_bytes.call_count >= 1  # Audio response
    
    @pytest.mark.asyncio
    async def test_handle_audio_data(self, websocket_manager, mock_websocket, sample_profile, sample_voice_config):
        """Test handling audio data for conversation processing."""
        session_id = "test_session_123"
        
        with patch('src.websocket_handler.ElevenLabsService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            
            # Mock conversation processing response
            mock_response = {
                "session_id": session_id,
                "response_text": "I heard you loud and clear!",
                "response_audio": b"fake_response_audio",
                "audio_format": "mp3",
                "voice_id": "test_voice_123"
            }
            mock_service.process_conversation_input.return_value = mock_response
            
            # Connect with profile and voice config
            await websocket_manager.connect(mock_websocket, session_id, sample_profile, sample_voice_config)
            
            # Handle audio data
            audio_data = b"fake_user_audio_input"
            await websocket_manager.handle_audio_data(session_id, audio_data)
            
            # Verify audio processing
            mock_service.process_conversation_input.assert_called_once_with(
                session_id=session_id,
                audio_data=audio_data,
                audio_format="mp3"
            )
            
            # Verify responses were sent
            assert mock_websocket.send_text.call_count >= 3  # Connection + processing + text response
            assert mock_websocket.send_bytes.call_count >= 1  # Audio response
    
    @pytest.mark.asyncio
    async def test_handle_heartbeat_message(self, websocket_manager, mock_websocket):
        """Test handling heartbeat message."""
        session_id = "test_session_123"
        
        with patch('src.websocket_handler.ElevenLabsService'):
            # Connect first
            await websocket_manager.connect(mock_websocket, session_id)
            
            # Send heartbeat message
            heartbeat_message = {"type": "heartbeat"}
            await websocket_manager.handle_message(session_id, heartbeat_message)
            
            # Verify heartbeat response was sent
            assert mock_websocket.send_text.call_count >= 2  # Connection + heartbeat response
    
    @pytest.mark.asyncio
    async def test_handle_end_conversation_message(self, websocket_manager, mock_websocket):
        """Test handling end conversation message."""
        session_id = "test_session_123"
        
        with patch('src.websocket_handler.ElevenLabsService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            
            # Connect first
            await websocket_manager.connect(mock_websocket, session_id)
            
            # Send end conversation message
            end_message = {"type": "end_conversation"}
            
            # Use asyncio.sleep mock to avoid actual delay
            with patch('asyncio.sleep', new_callable=AsyncMock):
                await websocket_manager.handle_message(session_id, end_message)
            
            # Verify session was ended (may be called multiple times due to cleanup)
            assert mock_service.end_conversation_session.called
            assert mock_service.end_conversation_session.call_count >= 1
    
    def test_get_active_sessions(self, websocket_manager):
        """Test getting active session information."""
        # Initially no sessions
        sessions = websocket_manager.get_active_sessions()
        assert len(sessions) == 0
        
        # Add some mock session metadata
        session_1 = "session_1"
        session_2 = "session_2"
        
        websocket_manager.connection_metadata[session_1] = {
            "connected_at": time.time(),
            "last_activity": time.time(),
            "message_count": 5,
            "profile": None,
            "voice_config": None
        }
        
        websocket_manager.connection_metadata[session_2] = {
            "connected_at": time.time(),
            "last_activity": time.time(),
            "message_count": 10,
            "profile": "mock_profile",
            "voice_config": "mock_voice_config"
        }
        
        # Get sessions
        sessions = websocket_manager.get_active_sessions()
        
        assert len(sessions) == 2
        assert session_1 in sessions
        assert session_2 in sessions
        
        # Verify session info structure
        assert sessions[session_1]["message_count"] == 5
        assert sessions[session_1]["has_profile"] is False
        assert sessions[session_1]["has_voice_config"] is False
        
        assert sessions[session_2]["message_count"] == 10
        assert sessions[session_2]["has_profile"] is True
        assert sessions[session_2]["has_voice_config"] is True
    
    @pytest.mark.asyncio
    async def test_cleanup_inactive_sessions(self, websocket_manager):
        """Test cleanup of inactive sessions."""
        with patch('src.websocket_handler.ElevenLabsService'):
            # Create mock sessions with different activity times
            current_time = time.time()
            
            # Active session (recent activity)
            active_session = "active_session"
            websocket_manager.connection_metadata[active_session] = {
                "connected_at": current_time,
                "last_activity": current_time - 100,  # 100 seconds ago
                "message_count": 5,
                "profile": None,
                "voice_config": None
            }
            
            # Inactive session (old activity)
            inactive_session = "inactive_session"
            websocket_manager.connection_metadata[inactive_session] = {
                "connected_at": current_time - 4000,
                "last_activity": current_time - 4000,  # Over 1 hour ago
                "message_count": 3,
                "profile": None,
                "voice_config": None
            }
            
            # Mock the disconnect method to avoid actual WebSocket operations
            websocket_manager.disconnect = AsyncMock()
            
            # Run cleanup
            await websocket_manager.cleanup_inactive_sessions()
            
            # Verify inactive session was cleaned up
            websocket_manager.disconnect.assert_called_once_with(inactive_session)
    
    @pytest.mark.asyncio
    async def test_error_handling_invalid_message_type(self, websocket_manager, mock_websocket):
        """Test error handling for invalid message types."""
        session_id = "test_session_123"
        
        with patch('src.websocket_handler.ElevenLabsService'):
            # Connect first
            await websocket_manager.connect(mock_websocket, session_id)
            
            # Send message with invalid type
            invalid_message = {"type": "invalid_type", "data": "test"}
            await websocket_manager.handle_message(session_id, invalid_message)
            
            # Verify error response was sent
            assert mock_websocket.send_text.call_count >= 2  # Connection + error response
            
            # Check that an error message was sent
            calls = mock_websocket.send_text.call_args_list
            error_call = calls[-1]  # Last call should be the error
            error_data = json.loads(error_call[0][0])
            
            assert error_data["type"] == "error"
            assert "unknown_message_type" in error_data["error"]