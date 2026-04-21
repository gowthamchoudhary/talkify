"""
WebSocket handler for real-time conversation with ElevenLabs Conversational AI.

This module provides WebSocket endpoints for real-time voice conversation
between users and AI characters, maintaining session state and context.

Requirements: 5.1, 5.4, 5.8, 10.6, 11.3
"""
import json
import logging
import asyncio
import time
from typing import Dict, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState

from .services.elevenlabs_service import ElevenLabsService
from .models import ObjectProfile, VoiceConfig, VoiceStyle
from .exceptions import ElevenLabsError

logger = logging.getLogger(__name__)


class ConversationWebSocketManager:
    """
    WebSocket manager for real-time conversation sessions.
    
    Handles WebSocket connections, message routing, and session management
    for voice conversations with AI characters.
    """
    
    def __init__(self):
        """Initialize the WebSocket manager."""
        self.active_connections: Dict[str, WebSocket] = {}
        self.session_services: Dict[str, ElevenLabsService] = {}
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Connection management settings
        self.heartbeat_interval = 30  # seconds
        self.max_message_size = 10 * 1024 * 1024  # 10MB for audio data
        self.session_timeout = 3600  # 1 hour
    
    async def connect(
        self, 
        websocket: WebSocket, 
        session_id: str,
        profile: Optional[ObjectProfile] = None,
        voice_config: Optional[VoiceConfig] = None
    ) -> bool:
        """
        Accept WebSocket connection and initialize conversation session.
        
        Args:
            websocket: WebSocket connection
            session_id: Unique session identifier
            profile: Object character profile (optional, can be set later)
            voice_config: Voice configuration (optional, can be set later)
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            await websocket.accept()
            
            # Store connection
            self.active_connections[session_id] = websocket
            
            # Initialize ElevenLabs service for this session
            service = ElevenLabsService()
            await service.__aenter__()
            self.session_services[session_id] = service
            
            # Store connection metadata
            self.connection_metadata[session_id] = {
                "connected_at": time.time(),
                "last_activity": time.time(),
                "profile": profile,
                "voice_config": voice_config,
                "message_count": 0
            }
            
            # Start conversation session if profile and voice are provided
            if profile and voice_config:
                await service.start_conversation_session(profile, voice_config)
            
            logger.info(f"WebSocket connected for session {session_id}")
            
            # Send connection confirmation
            await self.send_message(session_id, {
                "type": "connection_established",
                "session_id": session_id,
                "timestamp": time.time(),
                "status": "ready" if (profile and voice_config) else "waiting_for_setup"
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect WebSocket for session {session_id}: {e}")
            return False
    
    async def disconnect(self, session_id: str):
        """
        Disconnect WebSocket and clean up session resources.
        
        Args:
            session_id: Session to disconnect
        """
        try:
            # Close ElevenLabs service
            if session_id in self.session_services:
                service = self.session_services[session_id]
                await service.end_conversation_session(session_id)
                await service.__aexit__(None, None, None)
                del self.session_services[session_id]
            
            # Remove connection
            if session_id in self.active_connections:
                websocket = self.active_connections[session_id]
                if websocket.client_state != WebSocketState.DISCONNECTED:
                    await websocket.close()
                del self.active_connections[session_id]
            
            # Clean up metadata
            if session_id in self.connection_metadata:
                del self.connection_metadata[session_id]
            
            logger.info(f"WebSocket disconnected for session {session_id}")
            
        except Exception as e:
            logger.error(f"Error during WebSocket disconnect for session {session_id}: {e}")
    
    async def send_message(self, session_id: str, message: Dict[str, Any]) -> bool:
        """
        Send message to WebSocket client.
        
        Args:
            session_id: Target session
            message: Message data to send
            
        Returns:
            True if message sent successfully, False otherwise
        """
        try:
            if session_id not in self.active_connections:
                logger.warning(f"No active connection for session {session_id}")
                return False
            
            websocket = self.active_connections[session_id]
            
            # Add timestamp to message
            message["timestamp"] = time.time()
            
            # Send as JSON
            await websocket.send_text(json.dumps(message))
            
            # Update activity timestamp
            if session_id in self.connection_metadata:
                self.connection_metadata[session_id]["last_activity"] = time.time()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message to session {session_id}: {e}")
            await self.disconnect(session_id)
            return False
    
    async def send_audio(self, session_id: str, audio_data: bytes, metadata: Dict[str, Any]) -> bool:
        """
        Send audio data to WebSocket client.
        
        Args:
            session_id: Target session
            audio_data: Audio bytes to send
            metadata: Audio metadata (format, duration, etc.)
            
        Returns:
            True if audio sent successfully, False otherwise
        """
        try:
            if session_id not in self.active_connections:
                logger.warning(f"No active connection for session {session_id}")
                return False
            
            websocket = self.active_connections[session_id]
            
            # Send metadata first
            await websocket.send_text(json.dumps({
                "type": "audio_response",
                "metadata": metadata,
                "timestamp": time.time()
            }))
            
            # Send audio data as bytes
            await websocket.send_bytes(audio_data)
            
            # Update activity timestamp
            if session_id in self.connection_metadata:
                self.connection_metadata[session_id]["last_activity"] = time.time()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send audio to session {session_id}: {e}")
            await self.disconnect(session_id)
            return False
    
    async def handle_message(self, session_id: str, message: Dict[str, Any]):
        """
        Handle incoming WebSocket message.
        
        Args:
            session_id: Source session
            message: Received message data
        """
        try:
            message_type = message.get("type")
            
            if message_type == "setup_conversation":
                await self._handle_setup_conversation(session_id, message)
            elif message_type == "audio_input":
                await self._handle_audio_input(session_id, message)
            elif message_type == "text_input":
                await self._handle_text_input(session_id, message)
            elif message_type == "heartbeat":
                await self._handle_heartbeat(session_id, message)
            elif message_type == "end_conversation":
                await self._handle_end_conversation(session_id, message)
            else:
                logger.warning(f"Unknown message type '{message_type}' from session {session_id}")
                await self.send_message(session_id, {
                    "type": "error",
                    "error": "unknown_message_type",
                    "message": f"Unknown message type: {message_type}"
                })
            
            # Update message count
            if session_id in self.connection_metadata:
                self.connection_metadata[session_id]["message_count"] += 1
                self.connection_metadata[session_id]["last_activity"] = time.time()
            
        except Exception as e:
            logger.error(f"Error handling message from session {session_id}: {e}")
            await self.send_message(session_id, {
                "type": "error",
                "error": "message_processing_error",
                "message": str(e)
            })
    
    async def handle_audio_data(self, session_id: str, audio_data: bytes):
        """
        Handle incoming audio data for conversation processing.
        
        Args:
            session_id: Source session
            audio_data: Raw audio bytes
        """
        try:
            service = self.session_services.get(session_id)
            if not service:
                await self.send_message(session_id, {
                    "type": "error",
                    "error": "no_service",
                    "message": "No conversation service available for this session"
                })
                return
            
            # Send processing status
            await self.send_message(session_id, {
                "type": "processing_audio",
                "status": "analyzing_input"
            })
            
            # Process audio with ElevenLabs Conversational AI
            response = await service.process_conversation_input(
                session_id=session_id,
                audio_data=audio_data,
                audio_format="mp3"
            )
            
            # Send text response first
            await self.send_message(session_id, {
                "type": "text_response",
                "text": response["response_text"],
                "session_id": response["session_id"]
            })
            
            # Send audio response
            await self.send_audio(session_id, response["response_audio"], {
                "format": response["audio_format"],
                "voice_id": response["voice_id"],
                "text": response["response_text"]
            })
            
        except ElevenLabsError as e:
            logger.error(f"ElevenLabs error processing audio for session {session_id}: {e}")
            await self.send_message(session_id, {
                "type": "error",
                "error": "elevenlabs_error",
                "message": str(e)
            })
        except Exception as e:
            logger.error(f"Error processing audio for session {session_id}: {e}")
            await self.send_message(session_id, {
                "type": "error",
                "error": "audio_processing_error",
                "message": str(e)
            })
    
    async def _handle_setup_conversation(self, session_id: str, message: Dict[str, Any]):
        """Handle conversation setup message."""
        try:
            profile_data = message.get("profile")
            voice_config_data = message.get("voice_config")
            
            if not profile_data or not voice_config_data:
                await self.send_message(session_id, {
                    "type": "error",
                    "error": "missing_setup_data",
                    "message": "Profile and voice_config are required for setup"
                })
                return
            
            # Parse profile and voice config
            profile = ObjectProfile(**profile_data)
            voice_config = VoiceConfig(**voice_config_data)
            
            # Update metadata
            if session_id in self.connection_metadata:
                self.connection_metadata[session_id]["profile"] = profile
                self.connection_metadata[session_id]["voice_config"] = voice_config
            
            # Start conversation session
            service = self.session_services.get(session_id)
            if service:
                await service.start_conversation_session(profile, voice_config)
                
                await self.send_message(session_id, {
                    "type": "conversation_ready",
                    "profile": profile.model_dump(),
                    "voice_config": voice_config.model_dump()
                })
            else:
                await self.send_message(session_id, {
                    "type": "error",
                    "error": "no_service",
                    "message": "No conversation service available"
                })
                
        except Exception as e:
            logger.error(f"Error setting up conversation for session {session_id}: {e}")
            await self.send_message(session_id, {
                "type": "error",
                "error": "setup_error",
                "message": str(e)
            })
    
    async def _handle_audio_input(self, session_id: str, message: Dict[str, Any]):
        """Handle audio input message (metadata only, audio comes as bytes)."""
        await self.send_message(session_id, {
            "type": "audio_received",
            "status": "ready_for_audio_data"
        })
    
    async def _handle_text_input(self, session_id: str, message: Dict[str, Any]):
        """Handle text input for conversation."""
        try:
            text = message.get("text", "").strip()
            if not text:
                await self.send_message(session_id, {
                    "type": "error",
                    "error": "empty_text",
                    "message": "Text input cannot be empty"
                })
                return
            
            service = self.session_services.get(session_id)
            if not service:
                await self.send_message(session_id, {
                    "type": "error",
                    "error": "no_service",
                    "message": "No conversation service available"
                })
                return
            
            # Add user message to context
            service.add_conversation_message(session_id, f"User: {text}")
            
            # Generate response
            context = service.get_conversation_context(session_id)
            response_text = await service._generate_contextual_response(session_id, context)
            
            # Get voice config for TTS
            voice_config = self.connection_metadata[session_id].get("voice_config")
            if voice_config:
                # Convert response to speech
                audio_data = await service.text_to_speech_v3(
                    text=response_text,
                    voice_id=voice_config.voice_id,
                    voice_settings=voice_config.settings,
                    conversation_context=context,
                    audio_format="mp3"
                )
                
                # Send text response
                await self.send_message(session_id, {
                    "type": "text_response",
                    "text": response_text,
                    "user_input": text
                })
                
                # Send audio response
                await self.send_audio(session_id, audio_data, {
                    "format": "mp3",
                    "voice_id": voice_config.voice_id,
                    "text": response_text
                })
                
                # Add AI response to context
                service.add_conversation_message(session_id, f"AI: {response_text}")
            else:
                # Text-only response
                await self.send_message(session_id, {
                    "type": "text_response",
                    "text": response_text,
                    "user_input": text
                })
                
        except Exception as e:
            logger.error(f"Error handling text input for session {session_id}: {e}")
            await self.send_message(session_id, {
                "type": "error",
                "error": "text_processing_error",
                "message": str(e)
            })
    
    async def _handle_heartbeat(self, session_id: str, message: Dict[str, Any]):
        """Handle heartbeat message to keep connection alive."""
        await self.send_message(session_id, {
            "type": "heartbeat_response",
            "status": "alive"
        })
    
    async def _handle_end_conversation(self, session_id: str, message: Dict[str, Any]):
        """Handle conversation end request."""
        try:
            service = self.session_services.get(session_id)
            if service:
                await service.end_conversation_session(session_id)
            
            await self.send_message(session_id, {
                "type": "conversation_ended",
                "status": "session_closed"
            })
            
            # Disconnect after a brief delay
            await asyncio.sleep(1)
            await self.disconnect(session_id)
            
        except Exception as e:
            logger.error(f"Error ending conversation for session {session_id}: {e}")
            await self.disconnect(session_id)
    
    def get_active_sessions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all active sessions.
        
        Returns:
            Dictionary of session information
        """
        sessions = {}
        for session_id, metadata in self.connection_metadata.items():
            sessions[session_id] = {
                "connected_at": metadata["connected_at"],
                "last_activity": metadata["last_activity"],
                "message_count": metadata["message_count"],
                "has_profile": metadata.get("profile") is not None,
                "has_voice_config": metadata.get("voice_config") is not None,
                "active": session_id in self.active_connections
            }
        return sessions
    
    async def cleanup_inactive_sessions(self):
        """Clean up sessions that have been inactive for too long."""
        current_time = time.time()
        inactive_sessions = []
        
        for session_id, metadata in self.connection_metadata.items():
            if current_time - metadata["last_activity"] > self.session_timeout:
                inactive_sessions.append(session_id)
        
        for session_id in inactive_sessions:
            logger.info(f"Cleaning up inactive session {session_id}")
            await self.disconnect(session_id)


# Global WebSocket manager instance
websocket_manager = ConversationWebSocketManager()