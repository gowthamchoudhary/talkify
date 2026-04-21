"""
Music API integration for song generation.

This module provides music generation using ElevenLabs Music API
for creating songs with lyrics matching object personalities.

Requirements: 7.1, 7.2, 7.7, 11.5
"""
import logging
import uuid
from typing import Dict, Any, Optional
import asyncio

from ..elevenlabs_client import ElevenLabsClient
from ..models import ObjectProfile, Song
from ..exceptions import ElevenLabsError

logger = logging.getLogger(__name__)


class MusicGeneratorService:
    """
    Service for generating songs using ElevenLabs Music API.
    
    Handles:
    - Song lyrics generation based on personality
    - Music generation with character voice
    - Duration constraints (30-90 seconds)
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Music Generator service with ElevenLabs client."""
        self.client = ElevenLabsClient(api_key)
        
        # Song style mappings for different personalities
        self.style_mappings = {
            "playful": "upbeat and cheerful melody",
            "mysterious": "haunting and enigmatic tune",
            "wise": "thoughtful and contemplative melody",
            "dramatic": "powerful and theatrical composition",
            "gentle": "soft and soothing lullaby",
            "energetic": "fast-paced and exciting rhythm"
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.__aexit__(exc_type, exc_val, exc_tb)
    
    def _generate_song_lyrics(
        self,
        profile: ObjectProfile,
        theme: Optional[str] = None
    ) -> str:
        """
        Generate song lyrics based on object profile.
        
        Args:
            profile: Object character profile
            theme: Optional song theme
            
        Returns:
            Generated lyrics
        """
        # Create lyrics based on personality and backstory
        name = profile.name
        traits = ", ".join(profile.traits[:2])
        
        if theme:
            lyrics = f"""I'm {name}, {traits} and free,
{theme} is what defines me.
Through every day and every night,
I shine my own unique light.

{profile.backstory[:50]}...
That's my story, can't you see?
I'm {name}, just being me!"""
        else:
            lyrics = f"""Hello there, I'm {name},
{traits}, that's my game.
I've got a story to tell,
Listen close, listen well.

{profile.backstory[:50]}...
That's who I am, you see,
{name}, wild and free!"""
        
        return lyrics.strip()
    
    def _get_music_style(self, profile: ObjectProfile) -> str:
        """
        Determine music style from personality traits.
        
        Args:
            profile: Object character profile
            
        Returns:
            Music style description
        """
        traits_lower = [t.lower() for t in profile.traits]
        
        for trait in traits_lower:
            for key, style in self.style_mappings.items():
                if key in trait:
                    return style
        
        # Default style
        return "melodic and pleasant tune"
    
    async def generate_song(
        self,
        profile: ObjectProfile,
        voice_id: str,
        theme: Optional[str] = None,
        target_duration: float = 45.0
    ) -> Song:
        """
        Generate complete song with lyrics and music.
        
        Args:
            profile: Object character profile
            voice_id: ElevenLabs voice ID for singing
            theme: Optional song theme
            target_duration: Target duration in seconds (30-90)
            
        Returns:
            Song object with lyrics and audio
            
        Raises:
            ElevenLabsError: If song generation fails
        """
        try:
            # Validate duration constraint
            if not (30.0 <= target_duration <= 90.0):
                target_duration = max(30.0, min(90.0, target_duration))
                logger.warning(f"Duration adjusted to {target_duration}s (must be 30-90s)")
            
            # Generate lyrics
            lyrics = self._generate_song_lyrics(profile, theme)
            
            # Get music style
            music_style = self._get_music_style(profile)
            
            # Prepare request payload
            payload = {
                "text": lyrics,
                "voice_id": voice_id,
                "music_style": music_style,
                "duration_seconds": target_duration,
                "model_id": "eleven_multilingual_music_v1"
            }
            
            logger.info(f"Generating song for {profile.name}")
            logger.debug(f"Music style: {music_style}")
            
            # Call ElevenLabs Music API
            audio_data = await self.client.post_audio(
                "/music-generation",
                json_data=payload
            )
            
            # Create song object
            song = Song(
                id=f"song_{uuid.uuid4().hex[:12]}",
                title=f"{profile.name}'s Song",
                lyrics=lyrics,
                audio_url=f"/api/audio/song_{uuid.uuid4().hex[:12]}.mp3",
                duration=target_duration
            )
            
            logger.info(f"Generated song: {song.title} ({song.duration}s)")
            
            return song
            
        except Exception as e:
            logger.error(f"Failed to generate song: {e}")
            raise ElevenLabsError(f"Song generation failed: {str(e)}")
    
    def validate_song_duration(self, duration: float) -> bool:
        """
        Validate song duration is within constraints.
        
        Args:
            duration: Song duration in seconds
            
        Returns:
            True if duration is valid (30-90 seconds)
        """
        return 30.0 <= duration <= 90.0
    
    def create_lyrics_timestamps(
        self,
        lyrics: str,
        duration: float
    ) -> Dict[float, str]:
        """
        Create timestamp mapping for lyrics synchronization.
        
        Args:
            lyrics: Song lyrics
            duration: Total song duration
            
        Returns:
            Dictionary mapping timestamps to lyric lines
        """
        lines = [line.strip() for line in lyrics.split('\n') if line.strip()]
        
        if not lines:
            return {}
        
        # Distribute lines evenly across duration
        time_per_line = duration / len(lines)
        
        timestamps = {}
        for i, line in enumerate(lines):
            timestamp = i * time_per_line
            timestamps[timestamp] = line
        
        return timestamps


# Example usage
async def example_music_generation():
    """Example of how to use the Music Generator service."""
    from ..models import ObjectProfile, VoiceStyle
    
    # Create example profile
    profile = ObjectProfile(
        id="example-001",
        name="Melody",
        species="Violin",
        emoji="🎻",
        traits=["Dramatic", "Passionate", "Artistic"],
        backstory="An elegant violin crafted by a master luthier, capable of expressing the deepest emotions."
    )
    
    async with MusicGeneratorService() as service:
        # Generate song
        song = await service.generate_song(
            profile=profile,
            voice_id="demo_voice_123",
            theme="music and passion",
            target_duration=45.0
        )
        
        print(f"Generated: {song.title}")
        print(f"Duration: {song.duration}s")
        print(f"Lyrics:\n{song.lyrics}")
        
        # Create timestamps for synchronization
        timestamps = service.create_lyrics_timestamps(song.lyrics, song.duration)
        print(f"\nLyric timestamps: {len(timestamps)} lines")


if __name__ == "__main__":
    asyncio.run(example_music_generation())
