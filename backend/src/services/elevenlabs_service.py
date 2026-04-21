"""
ElevenLabs service integration using the base client.

This module provides comprehensive ElevenLabs API operations including
Voice Design API integration for creating unique character voices.
"""
from typing import Dict, Any, Optional, List
import logging
import uuid
import time

from ..elevenlabs_client import ElevenLabsClient
from ..models import VoiceConfig, VoiceStyle, ObjectProfile
from ..exceptions import ElevenLabsError

logger = logging.getLogger(__name__)


class ElevenLabsService:
    """
    High-level service for ElevenLabs API operations.
    
    This service uses the ElevenLabsClient base class to provide
    specific functionality for voice generation, TTS, conversational AI,
    sound effects, and music generation.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the service with ElevenLabs client."""
        self.client = ElevenLabsClient(api_key)
        
        # Voice style mappings for personality traits
        self.voice_style_mappings = {
            VoiceStyle.MYSTERIOUS: {
                "description_keywords": ["enigmatic", "secretive", "deep", "haunting", "whispered"],
                "voice_settings": {"stability": 0.7, "similarity_boost": 0.6, "style": 0.8}
            },
            VoiceStyle.WARM: {
                "description_keywords": ["friendly", "comforting", "gentle", "caring", "soothing"],
                "voice_settings": {"stability": 0.6, "similarity_boost": 0.7, "style": 0.3}
            },
            VoiceStyle.WISE: {
                "description_keywords": ["knowledgeable", "thoughtful", "mature", "experienced", "calm"],
                "voice_settings": {"stability": 0.8, "similarity_boost": 0.5, "style": 0.2}
            },
            VoiceStyle.PLAYFUL: {
                "description_keywords": ["energetic", "cheerful", "lively", "fun", "animated"],
                "voice_settings": {"stability": 0.4, "similarity_boost": 0.8, "style": 0.7}
            },
            VoiceStyle.DRAMATIC: {
                "description_keywords": ["theatrical", "expressive", "passionate", "intense", "bold"],
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.6, "style": 0.9}
            },
            VoiceStyle.WHISPERY: {
                "description_keywords": ["soft", "gentle", "intimate", "quiet", "breathy"],
                "voice_settings": {"stability": 0.9, "similarity_boost": 0.4, "style": 0.1}
            }
        }
        
        # Session storage for voice configurations
        self.voice_sessions: Dict[str, VoiceConfig] = {}
        
        # Conversation context storage for emotional analysis
        self.conversation_contexts: Dict[str, List[str]] = {}
        
        # Audio streaming settings
        self.streaming_chunk_size = 1024 * 4  # 4KB chunks for streaming
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.__aexit__(exc_type, exc_val, exc_tb)
    
    def _generate_voice_description(self, profile: ObjectProfile, style: VoiceStyle) -> str:
        """
        Generate voice description based on object profile and selected style.
        
        Args:
            profile: Object character profile
            style: Selected voice style
            
        Returns:
            Voice description for ElevenLabs Voice Design API
        """
        style_info = self.voice_style_mappings[style]
        keywords = style_info["description_keywords"]
        
        # Map personality traits to voice characteristics
        trait_mappings = {
            "curious": "inquisitive and wondering",
            "friendly": "warm and welcoming", 
            "wise": "knowledgeable and thoughtful",
            "playful": "energetic and fun-loving",
            "mysterious": "enigmatic and secretive",
            "gentle": "soft and caring",
            "bold": "confident and strong",
            "cheerful": "happy and upbeat",
            "calm": "peaceful and serene",
            "adventurous": "excited and daring"
        }
        
        # Build voice characteristics from personality traits
        voice_characteristics = []
        for trait in profile.traits:
            trait_lower = trait.lower()
            for key, description in trait_mappings.items():
                if key in trait_lower:
                    voice_characteristics.append(description)
                    break
            else:
                # If no direct mapping, use the trait itself
                voice_characteristics.append(trait_lower)
        
        # Combine style keywords with trait characteristics
        all_characteristics = keywords[:2] + voice_characteristics[:2]
        
        # Create description based on object type and characteristics
        if profile.species.lower() in ["animal", "pet", "creature"]:
            base_description = f"A {style.value} voice for a {profile.species.lower()} character named {profile.name}"
        else:
            base_description = f"A {style.value} voice for a {profile.species.lower()} object that has come to life as {profile.name}"
        
        characteristics_text = ", ".join(all_characteristics)
        
        return f"{base_description}. The voice should sound {characteristics_text}, reflecting the character's personality."
    
    async def create_voice_design(self, profile: ObjectProfile, style: VoiceStyle) -> VoiceConfig:
        """
        Create a unique voice using ElevenLabs Voice Design API.
        
        Args:
            profile: Object character profile
            style: Selected voice style
            
        Returns:
            VoiceConfig with generated voice ID and settings
            
        Raises:
            ElevenLabsError: If voice generation fails
        """
        try:
            # Generate voice description based on profile and style
            voice_description = self._generate_voice_description(profile, style)
            
            # Get style-specific voice settings
            style_settings = self.voice_style_mappings[style]["voice_settings"]
            
            # Prepare request payload for Voice Design API
            payload = {
                "text": f"Hello, I'm {profile.name}. {profile.backstory[:100]}...",
                "voice_description": voice_description,
                "model_id": "eleven_multilingual_v2"  # Use latest multilingual model
            }
            
            logger.info(f"Creating voice for {profile.name} with style {style.value}")
            
            # Call ElevenLabs Voice Design API
            response = await self.client.post("/voice-generation/generate-voice", json_data=payload)
            
            # Create voice configuration
            voice_config = VoiceConfig(
                voice_id=response["voice_id"],
                style=style,
                settings=style_settings
            )
            
            # Store in session for later use
            session_id = str(uuid.uuid4())
            self.voice_sessions[session_id] = voice_config
            
            logger.info(f"Successfully created voice {voice_config.voice_id} for {profile.name}")
            
            return voice_config
            
        except Exception as e:
            logger.error(f"Failed to create voice design: {e}")
            raise ElevenLabsError(f"Voice generation failed: {e}")
    
    def get_voice_style_options(self) -> List[Dict[str, Any]]:
        """
        Get available voice style options with descriptions.
        
        Returns:
            List of voice style options with metadata
        """
        options = []
        for style in VoiceStyle:
            style_info = self.voice_style_mappings[style]
            options.append({
                "style": style.value,
                "name": style.value.title(),
                "description": f"A {style.value} voice with {', '.join(style_info['description_keywords'][:3])} characteristics",
                "keywords": style_info["description_keywords"]
            })
        return options
    
    def store_voice_config(self, session_id: str, voice_config: VoiceConfig) -> None:
        """
        Store voice configuration for session use.
        
        Args:
            session_id: Session identifier
            voice_config: Voice configuration to store
        """
        self.voice_sessions[session_id] = voice_config
        logger.info(f"Stored voice config for session {session_id}")
    
    def get_voice_config(self, session_id: str) -> Optional[VoiceConfig]:
        """
        Retrieve voice configuration from session storage.
        
        Args:
            session_id: Session identifier
            
        Returns:
            VoiceConfig if found, None otherwise
        """
        return self.voice_sessions.get(session_id)
    
    def clear_voice_session(self, session_id: str) -> bool:
        """
        Clear voice configuration from session storage.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session was found and cleared, False otherwise
        """
        if session_id in self.voice_sessions:
            del self.voice_sessions[session_id]
            logger.info(f"Cleared voice session {session_id}")
            return True
        return False
    
    def add_conversation_message(self, session_id: str, message: str, max_context: int = 10) -> None:
        """
        Add a message to conversation context for emotional analysis.
        
        Args:
            session_id: Session identifier
            message: Message text to add
            max_context: Maximum number of messages to keep in context
        """
        if session_id not in self.conversation_contexts:
            self.conversation_contexts[session_id] = []
        
        self.conversation_contexts[session_id].append(message)
        
        # Keep only the most recent messages
        if len(self.conversation_contexts[session_id]) > max_context:
            self.conversation_contexts[session_id] = self.conversation_contexts[session_id][-max_context:]
        
        logger.debug(f"Added message to conversation context for session {session_id}")
    
    def get_conversation_context(self, session_id: str) -> List[str]:
        """
        Get conversation context for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of recent conversation messages
        """
        return self.conversation_contexts.get(session_id, [])
    
    def clear_conversation_context(self, session_id: str) -> bool:
        """
        Clear conversation context for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if context was found and cleared, False otherwise
        """
        if session_id in self.conversation_contexts:
            del self.conversation_contexts[session_id]
            logger.info(f"Cleared conversation context for session {session_id}")
            return True
        return False
    
    async def convert_audio_format(self, audio_data: bytes, target_format: str = "mp3") -> bytes:
        """
        Convert audio data to different format if needed.
        
        Note: This is a placeholder for audio format conversion.
        In a production environment, you would use libraries like pydub or ffmpeg
        for actual audio format conversion.
        
        Args:
            audio_data: Original audio data
            target_format: Target audio format
            
        Returns:
            Converted audio data (currently returns original data)
        """
        # For now, return original data as ElevenLabs already provides the requested format
        # In production, implement actual conversion using pydub or similar
        logger.debug(f"Audio format conversion requested to {target_format}")
        return audio_data
    
    async def stream_audio_response(self, audio_data: bytes) -> bytes:
        """
        Prepare audio data for streaming response.
        
        Args:
            audio_data: Audio data to prepare for streaming
            
        Returns:
            Audio data optimized for streaming
        """
        # Add streaming headers or chunk the data if needed
        # For now, return the data as-is since ElevenLabs provides streaming-optimized audio
        logger.debug(f"Prepared {len(audio_data)} bytes for streaming")
        return audio_data
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.__aexit__(exc_type, exc_val, exc_tb)
    
    async def get_user_info(self) -> Dict[str, Any]:
        """
        Get user information and subscription details.
        
        Returns:
            User information from ElevenLabs API
        """
        try:
            return await self.client.get("/user")
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            raise ElevenLabsError(f"Failed to get user info: {e}")
    
    async def list_voices(self) -> Dict[str, Any]:
        """
        List available voices from ElevenLabs.
        
        Returns:
            List of available voices
        """
        try:
            return await self.client.get("/voices")
        except Exception as e:
            logger.error(f"Failed to list voices: {e}")
            raise ElevenLabsError(f"Failed to list voices: {e}")
    
    def _detect_emotional_tags(self, text: str, conversation_context: Optional[List[str]] = None) -> List[str]:
        """
        Detect emotional tags based on text content and conversation context.
        
        Args:
            text: Text to analyze for emotions
            conversation_context: Previous conversation messages for context
            
        Returns:
            List of emotional tags for TTS v3 API
        """
        emotional_keywords = {
            "excited": ["amazing", "wonderful", "fantastic", "incredible", "awesome", "wow", "great", "excellent"],
            "happy": ["happy", "joy", "cheerful", "delighted", "pleased", "glad", "smile", "laugh"],
            "sad": ["sad", "sorry", "disappointed", "upset", "hurt", "cry", "tears", "sorrow"],
            "angry": ["angry", "mad", "furious", "annoyed", "irritated", "frustrated", "rage"],
            "surprised": ["surprised", "shocked", "amazed", "astonished", "unexpected", "sudden"],
            "curious": ["wonder", "curious", "interesting", "question", "why", "how", "what", "explore"],
            "calm": ["calm", "peaceful", "serene", "relaxed", "gentle", "quiet", "soft"],
            "mysterious": ["mysterious", "secret", "hidden", "unknown", "strange", "enigmatic"],
            "playful": ["fun", "play", "silly", "joke", "tease", "mischief", "giggle"],
            "wise": ["wisdom", "knowledge", "understand", "learn", "experience", "ancient", "old"]
        }
        
        text_lower = text.lower()
        detected_emotions = []
        
        # Analyze current text for emotional content
        for emotion, keywords in emotional_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                detected_emotions.append(emotion)
        
        # Analyze conversation context if provided
        if conversation_context:
            context_text = " ".join(conversation_context[-3:]).lower()  # Last 3 messages
            for emotion, keywords in emotional_keywords.items():
                if any(keyword in context_text for keyword in keywords):
                    if emotion not in detected_emotions:
                        detected_emotions.append(emotion)
        
        # Default to calm if no emotions detected
        if not detected_emotions:
            detected_emotions = ["calm"]
        
        # Limit to 3 most relevant emotions for TTS v3
        return detected_emotions[:3]
    
    def _get_audio_format_settings(self, format_type: str = "mp3") -> Dict[str, Any]:
        """
        Get audio format settings for TTS v3 API.
        
        Args:
            format_type: Desired audio format (mp3, wav, pcm)
            
        Returns:
            Format settings for the API request
        """
        format_settings = {
            "mp3": {
                "output_format": "mp3_44100_128",
                "optimize_streaming_latency": 2,
                "use_speaker_boost": True
            },
            "wav": {
                "output_format": "pcm_44100",
                "optimize_streaming_latency": 1,
                "use_speaker_boost": False
            },
            "pcm": {
                "output_format": "pcm_22050",
                "optimize_streaming_latency": 0,
                "use_speaker_boost": False
            }
        }
        
        return format_settings.get(format_type, format_settings["mp3"])
    
    async def text_to_speech_v3(
        self, 
        text: str, 
        voice_id: str,
        voice_settings: Optional[Dict[str, float]] = None,
        conversation_context: Optional[List[str]] = None,
        audio_format: str = "mp3",
        enable_streaming: bool = True
    ) -> bytes:
        """
        Convert text to speech using ElevenLabs TTS v3 API with emotional tags.
        
        Args:
            text: Text to convert to speech
            voice_id: ElevenLabs voice ID
            voice_settings: Voice generation settings
            conversation_context: Previous conversation messages for emotional context
            audio_format: Output audio format (mp3, wav, pcm)
            enable_streaming: Enable streaming optimization
            
        Returns:
            Audio data as bytes
            
        Raises:
            ElevenLabsError: If TTS conversion fails
        """
        try:
            # Detect emotional tags based on text and context
            emotional_tags = self._detect_emotional_tags(text, conversation_context)
            
            # Get format-specific settings
            format_settings = self._get_audio_format_settings(audio_format)
            
            # Prepare TTS v3 payload with emotional tags
            payload = {
                "text": text,
                "model_id": "eleven_turbo_v2_5",  # Latest TTS v3 model
                "voice_settings": voice_settings or {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                    "style": 0.0,
                    "use_speaker_boost": format_settings["use_speaker_boost"]
                },
                "pronunciation_dictionary_locators": [],
                "seed": None,
                "previous_text": conversation_context[-1] if conversation_context else None,
                "next_text": None,
                "previous_request_ids": [],
                "response_format": format_settings["output_format"],
                "optimize_streaming_latency": format_settings["optimize_streaming_latency"],
                "output_format": format_settings["output_format"]
            }
            
            # Add emotional tags if detected
            if emotional_tags:
                # TTS v3 uses style parameter for emotional expression
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
                
                # Use the strongest emotion for style adjustment
                primary_emotion = emotional_tags[0]
                if primary_emotion in emotion_style_mapping:
                    payload["voice_settings"]["style"] = emotion_style_mapping[primary_emotion]
            
            logger.info(f"Converting text to speech with emotions: {emotional_tags}")
            
            # Use streaming endpoint for better performance
            endpoint = f"/text-to-speech/{voice_id}/stream" if enable_streaming else f"/text-to-speech/{voice_id}"
            
            return await self.client.post_audio(endpoint, json_data=payload)
            
        except Exception as e:
            logger.error(f"Failed to convert text to speech with TTS v3: {e}")
            raise ElevenLabsError(f"TTS v3 conversion failed: {e}")
    
    async def text_to_speech(
        self, 
        text: str, 
        voice_id: str,
        voice_settings: Optional[Dict[str, float]] = None
    ) -> bytes:
        """
        Convert text to speech using ElevenLabs TTS API (legacy method).
        
        This method is kept for backward compatibility. For new implementations,
        use text_to_speech_v3 which includes emotional tags and better audio quality.
        
        Args:
            text: Text to convert to speech
            voice_id: ElevenLabs voice ID
            voice_settings: Voice generation settings
            
        Returns:
            Audio data as bytes
        """
        return await self.text_to_speech_v3(
            text=text,
            voice_id=voice_id,
            voice_settings=voice_settings,
            enable_streaming=False
        )
    
    async def start_conversation_session(self, profile: ObjectProfile, voice_config: VoiceConfig) -> str:
        """
        Start a new conversation session with ElevenLabs Conversational AI.
        
        Args:
            profile: Object character profile for conversation context
            voice_config: Voice configuration for the character
            
        Returns:
            Session ID for the conversation
            
        Raises:
            ElevenLabsError: If conversation session creation fails
        """
        try:
            session_id = str(uuid.uuid4())
            
            # Initialize conversation context with character information
            initial_context = [
                f"You are {profile.name}, a {profile.species}.",
                f"Your personality traits are: {', '.join(profile.traits)}.",
                f"Your backstory: {profile.backstory}",
                "Respond in character, keeping your responses conversational and engaging."
            ]
            
            # Store conversation context and voice config for this session
            self.conversation_contexts[session_id] = initial_context
            self.voice_sessions[session_id] = voice_config
            
            logger.info(f"Started conversation session {session_id} for {profile.name}")
            
            return session_id
            
        except Exception as e:
            logger.error(f"Failed to start conversation session: {e}")
            raise ElevenLabsError(f"Conversation session creation failed: {e}")
    
    async def process_conversation_input(
        self, 
        session_id: str, 
        audio_data: bytes,
        audio_format: str = "mp3"
    ) -> Dict[str, Any]:
        """
        Process audio input using ElevenLabs Conversational AI.
        
        Args:
            session_id: Active conversation session ID
            audio_data: User's audio input as bytes
            audio_format: Audio format (mp3, wav, etc.)
            
        Returns:
            Dictionary containing AI response text and audio
            
        Raises:
            ElevenLabsError: If conversation processing fails
        """
        try:
            # Get voice configuration for this session
            voice_config = self.voice_sessions.get(session_id)
            if not voice_config:
                raise ElevenLabsError(f"No voice configuration found for session {session_id}")
            
            # Get conversation context
            conversation_context = self.conversation_contexts.get(session_id, [])
            
            # Use ElevenLabs Conversational AI to process the audio input
            # Note: This is a placeholder for the actual Conversational AI API call
            # The real implementation would use the ElevenLabs Conversational AI endpoint
            conversation_payload = {
                "audio": audio_data,
                "voice_id": voice_config.voice_id,
                "model_id": "eleven_turbo_v2_5",
                "response_format": "mp3_44100_128",
                "conversation_context": conversation_context[-5:],  # Last 5 messages for context
                "voice_settings": voice_config.settings
            }
            
            # For now, we'll simulate the conversational AI response
            # In production, this would be a call to ElevenLabs Conversational AI API
            logger.info(f"Processing conversation input for session {session_id}")
            
            # Simulate AI response generation based on context
            response_text = await self._generate_contextual_response(session_id, conversation_context)
            
            # Convert response to speech using TTS v3
            response_audio = await self.text_to_speech_v3(
                text=response_text,
                voice_id=voice_config.voice_id,
                voice_settings=voice_config.settings,
                conversation_context=conversation_context,
                audio_format=audio_format,
                enable_streaming=True
            )
            
            # Add response to conversation context
            self.add_conversation_message(session_id, f"AI: {response_text}")
            
            return {
                "session_id": session_id,
                "response_text": response_text,
                "response_audio": response_audio,
                "audio_format": audio_format,
                "voice_id": voice_config.voice_id,
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Failed to process conversation input: {e}")
            raise ElevenLabsError(f"Conversation processing failed: {e}")
    
    async def _generate_contextual_response(self, session_id: str, context: List[str]) -> str:
        """
        Generate contextual AI response based on conversation history.
        
        This is a placeholder implementation. In production, this would use
        ElevenLabs Conversational AI API to generate responses.
        
        Args:
            session_id: Conversation session ID
            context: Conversation context messages
            
        Returns:
            Generated response text
        """
        # Extract character information from context
        character_info = context[0] if context else "You are a friendly character."
        
        # Simple response generation based on context length
        if len(context) <= 4:  # Initial conversation
            responses = [
                "Hello there! It's wonderful to meet you. What would you like to talk about?",
                "Hi! I'm so excited to have a conversation with you. How are you doing today?",
                "Greetings! I'm delighted to chat with you. What's on your mind?",
                "Hello! What a pleasure to meet you. I'd love to hear what you're thinking about."
            ]
        else:
            # Ongoing conversation - more varied responses
            responses = [
                "That's really interesting! Tell me more about that.",
                "I see what you mean. What do you think about it?",
                "How fascinating! I'd love to hear your thoughts on this.",
                "That sounds intriguing. Can you share more details?",
                "I understand. What would you like to explore next?",
                "That's a great point! What else comes to mind?",
                "Wonderful! I'm enjoying our conversation. What else shall we discuss?"
            ]
        
        # Select response based on session ID for consistency
        import hashlib
        hash_obj = hashlib.md5(session_id.encode())
        response_index = int(hash_obj.hexdigest(), 16) % len(responses)
        
        return responses[response_index]
    
    async def end_conversation_session(self, session_id: str) -> bool:
        """
        End a conversation session and clean up resources.
        
        Args:
            session_id: Session ID to end
            
        Returns:
            True if session was found and ended, False otherwise
        """
        try:
            # Clear conversation context
            context_cleared = self.clear_conversation_context(session_id)
            
            # Clear voice configuration
            voice_cleared = self.clear_voice_session(session_id)
            
            if context_cleared or voice_cleared:
                logger.info(f"Ended conversation session {session_id}")
                return True
            else:
                logger.warning(f"Session {session_id} not found")
                return False
                
        except Exception as e:
            logger.error(f"Failed to end conversation session {session_id}: {e}")
            return False
    
    async def get_conversation_status(self, session_id: str) -> Dict[str, Any]:
        """
        Get status information for a conversation session.
        
        Args:
            session_id: Session ID to check
            
        Returns:
            Dictionary with session status information
        """
        voice_config = self.voice_sessions.get(session_id)
        context = self.conversation_contexts.get(session_id, [])
        
        return {
            "session_id": session_id,
            "active": session_id in self.voice_sessions,
            "voice_configured": voice_config is not None,
            "voice_id": voice_config.voice_id if voice_config else None,
            "voice_style": voice_config.style.value if voice_config else None,
            "context_messages": len(context),
            "last_activity": time.time() if context else None
        }
    
    async def generate_sound_effects(
        self,
        object_type: str,
        intensity: float = 0.3,
        duration_seconds: int = 30,
        audio_format: str = "mp3"
    ) -> bytes:
        """
        Generate ambient sound effects using ElevenLabs Sound Effects API.
        
        Args:
            object_type: Type of object for contextual sound generation
            intensity: Sound intensity level (0.0 to 1.0)
            duration_seconds: Duration of ambient sound in seconds
            audio_format: Output audio format (mp3, wav)
            
        Returns:
            Audio data as bytes
            
        Raises:
            ElevenLabsError: If sound effects generation fails
        """
        try:
            # Map object types to sound effect descriptions
            sound_descriptions = self._get_sound_description_for_object(object_type)
            
            # Prepare sound effects API payload
            payload = {
                "text": sound_descriptions["primary_description"],
                "duration_seconds": duration_seconds,
                "prompt_influence": intensity,
                "model": "sound-effects-v1"
            }
            
            # Add secondary sound layers for richer ambient experience
            if sound_descriptions.get("secondary_sounds"):
                payload["secondary_prompts"] = sound_descriptions["secondary_sounds"]
            
            logger.info(f"Generating ambient sounds for {object_type} with intensity {intensity}")
            
            # Call ElevenLabs Sound Effects API
            response = await self.client.post_audio("/sound-generation", json_data=payload)
            
            # Apply volume mixing to ensure proper levels for speech compatibility
            mixed_audio = await self._apply_ambient_volume_mixing(response, intensity)
            
            logger.info(f"Successfully generated {len(mixed_audio)} bytes of ambient audio for {object_type}")
            
            return mixed_audio
            
        except Exception as e:
            logger.error(f"Failed to generate sound effects for {object_type}: {e}")
            raise ElevenLabsError(f"Sound effects generation failed: {e}")
    
    def _get_sound_description_for_object(self, object_type: str) -> Dict[str, Any]:
        """
        Get sound effect descriptions based on object type.
        
        Args:
            object_type: Type of object for sound generation
            
        Returns:
            Dictionary with sound descriptions and parameters
        """
        # Comprehensive mapping of object types to ambient sound descriptions
        sound_mappings = {
            # Nature objects
            "tree": {
                "primary_description": "Gentle rustling of leaves in a soft breeze, distant bird songs, peaceful forest ambiance",
                "secondary_sounds": ["wind through branches", "occasional bird chirp"],
                "mood": "peaceful"
            },
            "flower": {
                "primary_description": "Soft buzzing of bees, gentle breeze, garden ambiance with distant nature sounds",
                "secondary_sounds": ["bee buzzing", "light wind"],
                "mood": "serene"
            },
            "rock": {
                "primary_description": "Subtle wind over stone, distant mountain echoes, cave-like reverb",
                "secondary_sounds": ["wind over stone", "distant echo"],
                "mood": "ancient"
            },
            "water": {
                "primary_description": "Gentle flowing water, soft ripples, peaceful stream sounds",
                "secondary_sounds": ["water droplets", "gentle current"],
                "mood": "flowing"
            },
            
            # Animals
            "cat": {
                "primary_description": "Soft purring, gentle breathing, cozy indoor ambiance",
                "secondary_sounds": ["distant purr", "soft footsteps"],
                "mood": "cozy"
            },
            "dog": {
                "primary_description": "Gentle panting, soft tail wagging sounds, warm home atmosphere",
                "secondary_sounds": ["distant tail wag", "content breathing"],
                "mood": "friendly"
            },
            "bird": {
                "primary_description": "Soft chirping, gentle wing flutters, peaceful aviary sounds",
                "secondary_sounds": ["wing flutter", "distant bird calls"],
                "mood": "light"
            },
            
            # Household objects
            "book": {
                "primary_description": "Soft page turning, quiet library ambiance, gentle paper rustling",
                "secondary_sounds": ["page turn", "paper rustle"],
                "mood": "studious"
            },
            "clock": {
                "primary_description": "Gentle ticking, soft mechanical sounds, peaceful time passage",
                "secondary_sounds": ["soft tick", "mechanical hum"],
                "mood": "rhythmic"
            },
            "lamp": {
                "primary_description": "Soft electrical hum, warm ambient glow sounds, cozy room atmosphere",
                "secondary_sounds": ["electrical hum", "warm buzz"],
                "mood": "warm"
            },
            "chair": {
                "primary_description": "Soft creaking, gentle wood settling, comfortable furniture sounds",
                "secondary_sounds": ["wood creak", "settling sounds"],
                "mood": "comfortable"
            },
            
            # Technology objects
            "phone": {
                "primary_description": "Soft electronic hum, gentle notification sounds, modern tech ambiance",
                "secondary_sounds": ["electronic hum", "soft beep"],
                "mood": "modern"
            },
            "computer": {
                "primary_description": "Gentle fan whirring, soft keyboard clicks, tech workspace ambiance",
                "secondary_sounds": ["fan whir", "soft click"],
                "mood": "productive"
            },
            
            # Food objects
            "apple": {
                "primary_description": "Soft crunching sounds, fresh orchard ambiance, gentle nature sounds",
                "secondary_sounds": ["soft crunch", "orchard breeze"],
                "mood": "fresh"
            },
            "coffee": {
                "primary_description": "Gentle brewing sounds, soft steam, cozy cafe ambiance",
                "secondary_sounds": ["steam hiss", "coffee drip"],
                "mood": "energizing"
            },
            
            # Vehicles
            "car": {
                "primary_description": "Soft engine purr, gentle road sounds, peaceful driving ambiance",
                "secondary_sounds": ["engine hum", "road noise"],
                "mood": "traveling"
            },
            
            # Musical instruments
            "piano": {
                "primary_description": "Soft key resonance, gentle string vibrations, musical room ambiance",
                "secondary_sounds": ["string resonance", "key echo"],
                "mood": "musical"
            },
            "guitar": {
                "primary_description": "Gentle string vibrations, soft acoustic resonance, musical ambiance",
                "secondary_sounds": ["string vibration", "wood resonance"],
                "mood": "melodic"
            }
        }
        
        # Get specific mapping or create generic one
        if object_type.lower() in sound_mappings:
            return sound_mappings[object_type.lower()]
        else:
            # Generic ambient sound for unknown objects
            return {
                "primary_description": f"Soft ambient sounds related to {object_type}, gentle atmospheric background",
                "secondary_sounds": ["soft ambiance", "gentle atmosphere"],
                "mood": "neutral"
            }
    
    async def _apply_ambient_volume_mixing(self, audio_data: bytes, intensity: float) -> bytes:
        """
        Apply volume mixing to ensure ambient sounds don't interfere with speech.
        
        This function ensures that ambient sounds are mixed at appropriate levels
        to complement rather than compete with speech audio.
        
        Args:
            audio_data: Original audio data
            intensity: Requested intensity level (0.0 to 1.0)
            
        Returns:
            Volume-adjusted audio data
        """
        try:
            # Calculate ambient volume level based on intensity
            # Ambient sounds should always be quieter than speech
            max_ambient_volume = 0.3  # Maximum 30% volume for ambient sounds
            ambient_volume = intensity * max_ambient_volume
            
            # In a production environment, you would use audio processing libraries
            # like pydub, librosa, or similar to actually adjust the volume
            # For now, we'll simulate the volume adjustment
            
            logger.debug(f"Applied ambient volume mixing: intensity={intensity}, volume={ambient_volume}")
            
            # Placeholder for actual audio processing
            # In production, implement actual volume adjustment:
            # from pydub import AudioSegment
            # audio = AudioSegment.from_mp3(io.BytesIO(audio_data))
            # adjusted_audio = audio - (20 - int(ambient_volume * 20))  # Reduce volume
            # return adjusted_audio.export(format="mp3").read()
            
            return audio_data
            
        except Exception as e:
            logger.warning(f"Failed to apply volume mixing, returning original audio: {e}")
            return audio_data
    
    async def create_contextual_ambient_mix(
        self,
        object_type: str,
        conversation_active: bool = False,
        intensity: float = 0.3,
        duration_seconds: int = 60
    ) -> bytes:
        """
        Create contextual ambient sound mix that adapts to conversation state.
        
        Args:
            object_type: Type of object for contextual sounds
            conversation_active: Whether a conversation is currently active
            intensity: Base intensity level
            duration_seconds: Duration of the ambient mix
            
        Returns:
            Contextual ambient audio mix
        """
        try:
            # Adjust intensity based on conversation state
            if conversation_active:
                # Reduce ambient intensity during conversations
                adjusted_intensity = intensity * 0.6  # 60% of requested intensity
                logger.info(f"Reducing ambient intensity for active conversation: {adjusted_intensity}")
            else:
                adjusted_intensity = intensity
            
            # Generate base ambient sounds
            ambient_audio = await self.generate_sound_effects(
                object_type=object_type,
                intensity=adjusted_intensity,
                duration_seconds=duration_seconds
            )
            
            # Apply conversation-aware mixing
            if conversation_active:
                # Apply additional processing for conversation compatibility
                ambient_audio = await self._apply_conversation_mixing(ambient_audio)
            
            return ambient_audio
            
        except Exception as e:
            logger.error(f"Failed to create contextual ambient mix: {e}")
            raise ElevenLabsError(f"Contextual ambient mix creation failed: {e}")
    
    async def _apply_conversation_mixing(self, audio_data: bytes) -> bytes:
        """
        Apply additional audio processing for conversation compatibility.
        
        This ensures ambient sounds work well with real-time conversation audio.
        
        Args:
            audio_data: Original ambient audio
            
        Returns:
            Conversation-optimized audio
        """
        try:
            # In production, this would apply:
            # - High-pass filtering to remove low frequencies that interfere with speech
            # - Dynamic range compression to maintain consistent levels
            # - Stereo width adjustment for better spatial separation
            
            logger.debug("Applied conversation-specific audio processing")
            return audio_data
            
        except Exception as e:
            logger.warning(f"Failed to apply conversation mixing: {e}")
            return audio_data
    
    async def get_available_ambient_types(self) -> List[Dict[str, Any]]:
        """
        Get list of available ambient sound types with descriptions.
        
        Returns:
            List of ambient sound types with metadata
        """
        sound_mappings = self._get_sound_description_for_object("dummy")  # Get the mappings
        
        # Get all available types from the mapping
        available_types = []
        
        # Sample some common types to demonstrate capabilities
        sample_types = [
            "tree", "flower", "rock", "water", "cat", "dog", "bird",
            "book", "clock", "lamp", "chair", "phone", "computer",
            "apple", "coffee", "car", "piano", "guitar"
        ]
        
        for object_type in sample_types:
            sound_info = self._get_sound_description_for_object(object_type)
            available_types.append({
                "object_type": object_type,
                "description": sound_info["primary_description"],
                "mood": sound_info["mood"],
                "secondary_sounds": sound_info.get("secondary_sounds", [])
            })
        
        return available_types
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on ElevenLabs service.
        
        Returns:
            Health check results
        """
        return await self.client.health_check()


# Example usage function
async def example_voice_design_usage():
    """Example of how to use the Voice Design functionality."""
    async with ElevenLabsService() as service:
        # Check service health
        health = await service.health_check()
        print(f"Service health: {health}")
        
        # Get available voice style options
        voice_options = service.get_voice_style_options()
        print(f"Available voice styles: {[opt['name'] for opt in voice_options]}")
        
        # Create example object profile
        from ..models import ObjectProfile
        example_profile = ObjectProfile(
            id="test-123",
            name="Whiskers",
            species="Cat",
            emoji="🐱",
            traits=["Curious", "Playful", "Wise"],
            backstory="A mysterious cat who has seen many adventures and loves to share stories with anyone who will listen."
        )
        
        # Create voice with different styles
        for style in [VoiceStyle.MYSTERIOUS, VoiceStyle.PLAYFUL]:
            try:
                voice_config = await service.create_voice_design(example_profile, style)
                print(f"Created {style.value} voice: {voice_config.voice_id}")
                
                # Store in session
                session_id = f"session-{style.value}"
                service.store_voice_config(session_id, voice_config)
                
                # Retrieve from session
                retrieved_config = service.get_voice_config(session_id)
                print(f"Retrieved voice config: {retrieved_config.voice_id if retrieved_config else 'Not found'}")
                
            except ElevenLabsError as e:
                print(f"Failed to create {style.value} voice: {e}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_voice_design_usage())