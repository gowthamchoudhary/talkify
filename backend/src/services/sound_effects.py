"""
Sound Effects API integration for ambient audio generation.

This module provides sound effects generation using ElevenLabs Sound Effects API
for creating contextual background audio during conversations.

Requirements: 6.1, 6.2, 6.4, 11.4
"""
import logging
from typing import Dict, Any, Optional
import asyncio

from ..elevenlabs_client import ElevenLabsClient
from ..exceptions import ElevenLabsError

logger = logging.getLogger(__name__)


class SoundEffectsService:
    """
    Service for generating ambient sound effects using ElevenLabs Sound Effects API.
    
    Handles:
    - Ambient sound generation based on object type
    - Volume mixing to ensure speech clarity
    - Contextual background audio creation
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Sound Effects service with ElevenLabs client."""
        self.client = ElevenLabsClient(api_key)
        
        # Sound effect mappings for different object types
        self.sound_mappings = {
            # Nature sounds
            "forest": "gentle forest ambience with birds chirping and leaves rustling",
            "ocean": "calm ocean waves with seagulls in the distance",
            "rain": "soft rain falling with distant thunder",
            "wind": "gentle wind blowing through trees",
            "river": "flowing river water with nature sounds",
            
            # Animal sounds
            "cat": "soft purring and gentle meowing",
            "dog": "friendly dog sounds with tail wagging",
            "bird": "cheerful bird songs and wing fluttering",
            
            # Indoor sounds
            "library": "quiet library ambience with page turning",
            "cafe": "cozy cafe atmosphere with soft chatter",
            "home": "warm home ambience with subtle household sounds",
            
            # Magical/mysterious
            "magic": "mystical magical ambience with sparkles",
            "ancient": "ancient temple atmosphere with echoes",
            "mysterious": "mysterious ambient sounds with whispers",
            
            # Default
            "default": "soft ambient background with gentle atmosphere"
        }
        
        # Volume settings for proper mixing
        self.ambient_volume = 0.3  # 30% volume for ambient sounds
        self.speech_volume = 1.0   # 100% volume for speech
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.__aexit__(exc_type, exc_val, exc_tb)
    
    def _get_sound_description(self, object_type: str) -> str:
        """
        Get sound effect description for object type.
        
        Args:
            object_type: Type of object for sound generation
            
        Returns:
            Sound description for ElevenLabs API
        """
        object_lower = object_type.lower()
        
        # Check for direct matches
        for key, description in self.sound_mappings.items():
            if key in object_lower:
                return description
        
        # Generate contextual description
        return f"ambient background sounds suitable for a {object_type}"
    
    async def generate_ambient_sound(
        self,
        object_type: str,
        duration: float = 30.0,
        intensity: float = 0.3
    ) -> bytes:
        """
        Generate ambient sound effects for object type.
        
        Args:
            object_type: Type of object for contextual sounds
            duration: Duration of sound effect in seconds
            intensity: Sound intensity (0.0-1.0)
            
        Returns:
            Audio data as bytes
            
        Raises:
            ElevenLabsError: If sound generation fails
        """
        try:
            # Get sound description
            sound_description = self._get_sound_description(object_type)
            
            # Prepare request payload
            payload = {
                "text": sound_description,
                "duration_seconds": min(duration, 60.0),  # Max 60 seconds
                "prompt_influence": intensity
            }
            
            logger.info(f"Generating ambient sound for {object_type}")
            logger.debug(f"Sound description: {sound_description}")
            
            # Call ElevenLabs Sound Effects API
            audio_data = await self.client.post_audio(
                "/sound-generation",
                json_data=payload
            )
            
            # Apply volume adjustment for proper mixing
            adjusted_audio = self._adjust_volume(audio_data, self.ambient_volume)
            
            logger.info(f"Generated {len(adjusted_audio)} bytes of ambient audio")
            
            return adjusted_audio
            
        except Exception as e:
            logger.error(f"Failed to generate ambient sound: {e}")
            raise ElevenLabsError(f"Sound generation failed: {str(e)}")
    
    def _adjust_volume(self, audio_data: bytes, volume_factor: float) -> bytes:
        """
        Adjust audio volume for proper mixing with speech.
        
        Args:
            audio_data: Original audio data
            volume_factor: Volume adjustment factor (0.0-1.0)
            
        Returns:
            Volume-adjusted audio data
        """
        # For now, return original data
        # In production, implement actual volume adjustment using pydub or similar
        logger.debug(f"Volume adjustment: {volume_factor}")
        return audio_data
    
    def ensure_speech_clarity(
        self,
        ambient_volume: float,
        speech_volume: float
    ) -> bool:
        """
        Ensure ambient sounds don't interfere with speech.
        
        Args:
            ambient_volume: Ambient sound volume level
            speech_volume: Speech volume level
            
        Returns:
            True if volume relationship is correct
        """
        # Ambient should always be lower than speech
        return ambient_volume < speech_volume
    
    def get_recommended_volume(self, object_type: str) -> float:
        """
        Get recommended ambient volume for object type.
        
        Args:
            object_type: Type of object
            
        Returns:
            Recommended volume level (0.0-1.0)
        """
        # Quieter sounds for delicate objects
        quiet_types = ["flower", "baby", "whisper", "library"]
        if any(t in object_type.lower() for t in quiet_types):
            return 0.2
        
        # Louder sounds for energetic objects
        loud_types = ["storm", "ocean", "music", "party"]
        if any(t in object_type.lower() for t in loud_types):
            return 0.4
        
        # Default moderate volume
        return 0.3


# Example usage
async def example_sound_effects_usage():
    """Example of how to use the Sound Effects service."""
    async with SoundEffectsService() as service:
        # Generate ambient sound for a forest object
        audio_data = await service.generate_ambient_sound(
            object_type="forest",
            duration=30.0,
            intensity=0.3
        )
        
        print(f"Generated {len(audio_data)} bytes of forest ambience")
        
        # Check volume relationship
        is_clear = service.ensure_speech_clarity(
            ambient_volume=0.3,
            speech_volume=1.0
        )
        print(f"Speech clarity ensured: {is_clear}")


if __name__ == "__main__":
    asyncio.run(example_sound_effects_usage())
