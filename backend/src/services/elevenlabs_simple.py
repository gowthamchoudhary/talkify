"""
Simple ElevenLabs integration using direct API calls.
Based on ElevenLabs Power documentation.
"""

import asyncio
import aiohttp
import json
import logging
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class SimpleElevenLabsClient:
    """Simple ElevenLabs client using direct API calls."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise ValueError("ElevenLabs API key is required")
        
        self.base_url = "https://api.elevenlabs.io/v1"
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def text_to_speech(
        self,
        text: str,
        voice_id: str = "21m00Tcm4TlvDq8ikWAM",  # Rachel
        model_id: str = "eleven_flash_v2_5",
        voice_settings: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """
        Convert text to speech using ElevenLabs TTS API.
        
        Args:
            text: Text to convert
            voice_id: ElevenLabs voice ID
            model_id: Model to use (eleven_flash_v2_5 for low latency)
            voice_settings: Voice configuration
            
        Returns:
            Audio data as bytes
        """
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")
        
        url = f"{self.base_url}/text-to-speech/{voice_id}"
        
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "text": text,
            "model_id": model_id,
            "voice_settings": voice_settings or {
                "stability": 0.5,
                "similarity_boost": 0.8,
                "style": 0.9,
                "use_speaker_boost": True
            }
        }
        
        logger.info(f"Converting text to speech: {text[:50]}...")
        
        async with self.session.post(url, json=payload, headers=headers) as response:
            if response.status == 200:
                audio_data = await response.read()
                logger.info(f"TTS successful: {len(audio_data)} bytes")
                return audio_data
            else:
                error_text = await response.text()
                logger.error(f"TTS failed: {response.status} - {error_text}")
                raise Exception(f"TTS failed: {error_text}")
    
    async def generate_music(
        self,
        prompt: str,
        music_length_ms: int = 30000,
        model_id: str = "music_v1"
    ) -> bytes:
        """
        Generate music using ElevenLabs Music API.
        
        Args:
            prompt: Music description
            music_length_ms: Duration in milliseconds
            model_id: Music model to use
            
        Returns:
            Audio data as bytes
        """
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")
        
        url = f"{self.base_url}/music/detailed"
        
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "prompt": prompt,
            "music_length_ms": music_length_ms,
            "model_id": model_id,
            "force_instrumental": False
        }
        
        logger.info(f"Generating music: {prompt}")
        
        async with self.session.post(url, json=payload, headers=headers) as response:
            if response.status == 200:
                # Music API returns multipart response
                content_type = response.headers.get('content-type', '')
                if 'multipart' in content_type:
                    # For now, return the raw multipart data
                    # In production, you'd parse this properly
                    audio_data = await response.read()
                    logger.info(f"Music generation successful: {len(audio_data)} bytes")
                    return audio_data
                else:
                    # Fallback for non-multipart
                    audio_data = await response.read()
                    return audio_data
            else:
                error_text = await response.text()
                logger.error(f"Music generation failed: {response.status} - {error_text}")
                raise Exception(f"Music generation failed: {error_text}")


# Test functions
async def test_tts():
    """Test TTS functionality."""
    async with SimpleElevenLabsClient() as client:
        audio = await client.text_to_speech(
            "♪ Hello, I'm a singing coffee mug! ♪",
            voice_id="21m00Tcm4TlvDq8ikWAM"
        )
        
        with open("test_simple_tts.mp3", "wb") as f:
            f.write(audio)
        
        print(f"✅ TTS test successful: {len(audio)} bytes saved to test_simple_tts.mp3")


async def test_music():
    """Test music generation."""
    async with SimpleElevenLabsClient() as client:
        audio = await client.generate_music(
            "An upbeat cheerful song about a coffee mug",
            music_length_ms=30000
        )
        
        with open("test_simple_music.mp3", "wb") as f:
            f.write(audio)
        
        print(f"✅ Music test successful: {len(audio)} bytes saved to test_simple_music.mp3")


if __name__ == "__main__":
    print("Testing Simple ElevenLabs Client...")
    asyncio.run(test_tts())
    asyncio.run(test_music())