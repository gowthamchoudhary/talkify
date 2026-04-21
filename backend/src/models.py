"""
Pydantic models for VoiceSnap API requests and responses.
"""
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, field_validator
import time
import re


class VoiceStyle(str, Enum):
    """Available voice styles for character voices."""
    MYSTERIOUS = "mysterious"
    WARM = "warm"
    WISE = "wise"
    PLAYFUL = "playful"
    DRAMATIC = "dramatic"
    WHISPERY = "whispery"


class APIResponse(BaseModel):
    """Standard API response format."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, str]] = None
    timestamp: float = Field(default_factory=time.time)


class ErrorResponse(BaseModel):
    """Error response format."""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ObjectIdentification(BaseModel):
    """Object identification result from Gemini Vision API."""
    object_type: str = Field(..., description="Type of object identified")
    species: Optional[str] = Field(None, description="Species if living thing")
    characteristics: List[str] = Field(..., description="Descriptive characteristics")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")


class VoiceConfig(BaseModel):
    """Voice configuration for character."""
    voice_id: str = Field(..., min_length=1, description="ElevenLabs voice ID")
    style: VoiceStyle = Field(..., description="Voice style selection")
    settings: Dict[str, Union[float, int]] = Field(
        default_factory=lambda: {
            "stability": 0.5,
            "similarity_boost": 0.5,
            "style": 0.0
        },
        description="Voice generation settings"
    )
    
    @field_validator('settings')
    @classmethod
    def validate_voice_settings(cls, v):
        """Ensure voice settings are within valid ranges."""
        if 'stability' in v:
            if not 0.0 <= v['stability'] <= 1.0:
                raise ValueError("Stability must be between 0.0 and 1.0")
        if 'similarity_boost' in v:
            if not 0.0 <= v['similarity_boost'] <= 1.0:
                raise ValueError("Similarity boost must be between 0.0 and 1.0")
        if 'style' in v:
            if not 0.0 <= v['style'] <= 1.0:
                raise ValueError("Style must be between 0.0 and 1.0")
        return v


class ObjectProfile(BaseModel):
    """Complete object character profile."""
    id: str = Field(..., description="Unique profile identifier")
    name: str = Field(..., min_length=1, description="Generated character name")
    species: str = Field(..., min_length=1, description="Object type or species")
    emoji: str = Field(..., min_length=1, description="Representative emoji")
    traits: List[str] = Field(
        ..., 
        min_length=3, 
        max_length=3, 
        description="Exactly 3 personality traits"
    )
    backstory: str = Field(..., min_length=10, description="Character backstory paragraph")
    voice_config: Optional[VoiceConfig] = Field(None, description="Voice configuration")
    
    @field_validator('traits')
    @classmethod
    def validate_traits_not_empty(cls, v):
        """Ensure all traits are non-empty strings."""
        if not all(trait.strip() for trait in v):
            raise ValueError("All personality traits must be non-empty")
        return v
    
    @field_validator('name', 'species', 'backstory')
    @classmethod
    def validate_non_empty_strings(cls, v):
        """Ensure critical string fields are not just whitespace."""
        if not v.strip():
            raise ValueError("Field cannot be empty or just whitespace")
        return v.strip()


class ConversationMessage(BaseModel):
    """Individual conversation message."""
    id: str = Field(..., description="Message identifier")
    speaker: str = Field(..., description="Speaker: 'user' or 'object'")
    content: str = Field(..., description="Message text content")
    timestamp: float = Field(default_factory=time.time, description="Message timestamp")
    audio_url: Optional[str] = Field(None, description="Audio file URL if available")


class ConversationResponse(BaseModel):
    """Response from conversation processing."""
    text: str = Field(..., description="AI response text")
    audio_url: str = Field(..., description="Generated speech audio URL")
    session_id: str = Field(..., description="Conversation session ID")
    timestamp: float = Field(default_factory=time.time, description="Response timestamp")


class Song(BaseModel):
    """Generated song data."""
    id: str = Field(..., description="Song identifier")
    title: str = Field(..., min_length=1, description="Song title")
    lyrics: str = Field(..., min_length=1, description="Song lyrics")
    audio_url: str = Field(..., min_length=1, description="Song audio file URL")
    duration: float = Field(
        ..., 
        ge=30.0, 
        le=90.0, 
        description="Song duration in seconds (30-90s)"
    )
    
    @field_validator('title', 'lyrics')
    @classmethod
    def validate_non_empty_content(cls, v):
        """Ensure title and lyrics are not just whitespace."""
        if not v.strip():
            raise ValueError("Field cannot be empty or just whitespace")
        return v.strip()


class HealthCheck(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="API version")
    environment: str = Field(..., description="Environment name")
    timestamp: float = Field(default_factory=time.time, description="Check timestamp")
    checks: Dict[str, Any] = Field(..., description="Individual health checks")


# Request models
class IdentifyRequest(BaseModel):
    """Request model for object identification."""
    # File will be handled as UploadFile in endpoint
    pass


class ProfileRequest(BaseModel):
    """Request model for profile generation."""
    identification: ObjectIdentification = Field(..., description="Object identification data")
    voice_style: Optional[VoiceStyle] = Field(None, description="Preferred voice style")


class SpeakRequest(BaseModel):
    """Request model for text-to-speech."""
    text: str = Field(..., min_length=1, max_length=1000, description="Text to convert to speech")
    voice_config: VoiceConfig = Field(..., description="Voice configuration")
    
    @field_validator('text')
    @classmethod
    def validate_text_content(cls, v):
        """Ensure text is not just whitespace."""
        if not v.strip():
            raise ValueError("Text cannot be empty or just whitespace")
        return v.strip()


class SingRequest(BaseModel):
    """Request model for song generation."""
    profile: ObjectProfile = Field(..., description="Object profile for song creation")
    theme: Optional[str] = Field(None, description="Optional song theme")


class AmbientRequest(BaseModel):
    """Request model for ambient sound generation."""
    object_type: str = Field(..., description="Object type for ambient sounds")
    intensity: float = Field(default=0.3, ge=0.0, le=1.0, description="Sound intensity")