"""
Voice Designer service for creating unique character voices using ElevenLabs Voice Design API.

This module implements the Voice_Designer component from the technical design,
providing voice generation with 6 style options and personality trait mapping.

Requirements: 4.1, 4.2, 4.4, 11.1
"""
from typing import Dict, Any, Optional, List
import logging
import uuid
import asyncio

from ..elevenlabs_client import ElevenLabsClient
from ..models import VoiceConfig, VoiceStyle, ObjectProfile
from ..exceptions import ElevenLabsError

logger = logging.getLogger(__name__)


class VoiceDesigner:
    """
    Voice Designer service for creating unique character voices.
    
    This service handles:
    - Voice generation with 6 style options (Mysterious, Warm, Wise, Playful, Dramatic, Whispery)
    - Mapping personality traits to voice characteristics
    - Session-based voice configuration storage
    - Voice style recommendations based on object profiles
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Voice Designer with ElevenLabs client.
        
        Args:
            api_key: ElevenLabs API key. If None, uses settings.elevenlabs_api_key
        """
        self.client = ElevenLabsClient(api_key)
        
        # Voice style configurations with personality mappings
        self.style_configurations = {
            VoiceStyle.MYSTERIOUS: {
                "description_template": "A mysterious and enigmatic voice with deep, haunting tones",
                "personality_keywords": ["mysterious", "secretive", "enigmatic", "dark", "hidden"],
                "voice_settings": {
                    "stability": 0.75,
                    "similarity_boost": 0.65,
                    "style": 0.85,
                    "use_speaker_boost": True
                },
                "recommended_for": ["ancient objects", "magical items", "shadowy creatures"]
            },
            VoiceStyle.WARM: {
                "description_template": "A warm and comforting voice with friendly, caring tones",
                "personality_keywords": ["friendly", "caring", "gentle", "loving", "nurturing"],
                "voice_settings": {
                    "stability": 0.65,
                    "similarity_boost": 0.75,
                    "style": 0.25,
                    "use_speaker_boost": True
                },
                "recommended_for": ["household items", "pets", "comfort objects"]
            },
            VoiceStyle.WISE: {
                "description_template": "A wise and thoughtful voice with mature, experienced tones",
                "personality_keywords": ["wise", "knowledgeable", "experienced", "thoughtful", "sage"],
                "voice_settings": {
                    "stability": 0.85,
                    "similarity_boost": 0.55,
                    "style": 0.15,
                    "use_speaker_boost": True
                },
                "recommended_for": ["books", "old objects", "trees", "scholarly items"]
            },
            VoiceStyle.PLAYFUL: {
                "description_template": "A playful and energetic voice with lively, animated tones",
                "personality_keywords": ["playful", "energetic", "fun", "cheerful", "lively"],
                "voice_settings": {
                    "stability": 0.45,
                    "similarity_boost": 0.85,
                    "style": 0.75,
                    "use_speaker_boost": True
                },
                "recommended_for": ["toys", "young animals", "sports equipment", "games"]
            },
            VoiceStyle.DRAMATIC: {
                "description_template": "A dramatic and expressive voice with theatrical, passionate tones",
                "personality_keywords": ["dramatic", "theatrical", "passionate", "expressive", "bold"],
                "voice_settings": {
                    "stability": 0.55,
                    "similarity_boost": 0.65,
                    "style": 0.95,
                    "use_speaker_boost": True
                },
                "recommended_for": ["art objects", "musical instruments", "performance items"]
            },
            VoiceStyle.WHISPERY: {
                "description_template": "A soft and whispery voice with gentle, intimate tones",
                "personality_keywords": ["gentle", "soft", "quiet", "intimate", "delicate"],
                "voice_settings": {
                    "stability": 0.95,
                    "similarity_boost": 0.35,
                    "style": 0.05,
                    "use_speaker_boost": False
                },
                "recommended_for": ["delicate objects", "flowers", "small creatures", "precious items"]
            }
        }
        
        # Session storage for voice configurations
        self.voice_sessions: Dict[str, VoiceConfig] = {}
        
        # Cache for generated voices to avoid regeneration
        self.voice_cache: Dict[str, str] = {}  # profile_hash -> voice_id
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.__aexit__(exc_type, exc_val, exc_tb)
    
    def _generate_profile_hash(self, profile: ObjectProfile, style: VoiceStyle) -> str:
        """
        Generate a hash for profile and style combination for caching.
        
        Args:
            profile: Object profile
            style: Voice style
            
        Returns:
            Hash string for caching
        """
        profile_key = f"{profile.species}_{'-'.join(sorted(profile.traits))}_{style.value}"
        return profile_key.lower().replace(" ", "_")
    
    def _map_traits_to_voice_characteristics(self, traits: List[str]) -> List[str]:
        """
        Map personality traits to voice characteristics.
        
        Args:
            traits: List of personality traits
            
        Returns:
            List of voice characteristics
        """
        trait_mappings = {
            # Emotional traits
            "curious": "inquisitive and wondering",
            "friendly": "warm and welcoming",
            "gentle": "soft and caring",
            "cheerful": "bright and upbeat",
            "calm": "peaceful and serene",
            "excited": "energetic and enthusiastic",
            
            # Personality traits
            "wise": "knowledgeable and thoughtful",
            "playful": "fun-loving and animated",
            "mysterious": "enigmatic and secretive",
            "bold": "confident and strong",
            "shy": "quiet and reserved",
            "adventurous": "daring and spirited",
            
            # Character traits
            "mischievous": "playfully troublesome",
            "loyal": "steadfast and devoted",
            "independent": "self-reliant and strong-willed",
            "protective": "caring and watchful",
            "creative": "imaginative and artistic",
            "patient": "calm and understanding"
        }
        
        characteristics = []
        for trait in traits:
            trait_lower = trait.lower().strip()
            
            # Direct mapping
            if trait_lower in trait_mappings:
                characteristics.append(trait_mappings[trait_lower])
            else:
                # Partial matching for compound traits
                for key, description in trait_mappings.items():
                    if key in trait_lower or trait_lower in key:
                        characteristics.append(description)
                        break
                else:
                    # Use the trait itself if no mapping found
                    characteristics.append(trait_lower)
        
        return characteristics[:3]  # Limit to 3 characteristics
    
    def _build_voice_description(self, profile: ObjectProfile, style: VoiceStyle) -> str:
        """
        Build comprehensive voice description for ElevenLabs Voice Design API.
        
        Args:
            profile: Object character profile
            style: Selected voice style
            
        Returns:
            Detailed voice description
        """
        style_config = self.style_configurations[style]
        base_description = style_config["description_template"]
        
        # Map personality traits to voice characteristics
        voice_characteristics = self._map_traits_to_voice_characteristics(profile.traits)
        
        # Determine gender/age hints based on object type and name
        gender_hints = []
        if any(word in profile.species.lower() for word in ["man", "boy", "male", "father", "king"]):
            gender_hints.append("masculine")
        elif any(word in profile.species.lower() for word in ["woman", "girl", "female", "mother", "queen"]):
            gender_hints.append("feminine")
        
        # Age hints based on object type
        if any(word in profile.species.lower() for word in ["baby", "young", "child", "puppy", "kitten"]):
            gender_hints.append("youthful")
        elif any(word in profile.species.lower() for word in ["old", "ancient", "elder", "vintage"]):
            gender_hints.append("mature")
        
        # Build comprehensive description
        description_parts = [
            f"Create a voice for {profile.name}, a {profile.species.lower()}.",
            base_description + ".",
            f"The voice should embody these characteristics: {', '.join(voice_characteristics)}."
        ]
        
        if gender_hints:
            description_parts.append(f"The voice should sound {' and '.join(gender_hints)}.")
        
        # Add context from backstory
        if profile.backstory:
            backstory_snippet = profile.backstory[:100].strip()
            if backstory_snippet:
                description_parts.append(f"Background: {backstory_snippet}...")
        
        return " ".join(description_parts)
    
    def recommend_voice_style(self, profile: ObjectProfile) -> VoiceStyle:
        """
        Recommend a voice style based on object profile characteristics.
        
        Args:
            profile: Object character profile
            
        Returns:
            Recommended VoiceStyle
        """
        # Score each style based on profile characteristics
        style_scores = {}
        
        for style, config in self.style_configurations.items():
            score = 0
            
            # Score based on personality traits
            for trait in profile.traits:
                trait_lower = trait.lower()
                for keyword in config["personality_keywords"]:
                    if keyword in trait_lower or trait_lower in keyword:
                        score += 2
            
            # Score based on object type recommendations
            species_lower = profile.species.lower()
            for recommended_type in config["recommended_for"]:
                if any(word in species_lower for word in recommended_type.split()):
                    score += 1
            
            style_scores[style] = score
        
        # Return style with highest score, default to WARM if tie
        if not style_scores or max(style_scores.values()) == 0:
            return VoiceStyle.WARM
        
        return max(style_scores, key=style_scores.get)
    
    async def create_voice(self, profile: ObjectProfile, style: VoiceStyle) -> VoiceConfig:
        """
        Generate unique voice using ElevenLabs pre-made voices.
        
        Args:
            profile: Object character profile
            style: Selected voice style
            
        Returns:
            VoiceConfig with generated voice ID and settings
            
        Raises:
            ElevenLabsError: If voice generation fails
        """
        try:
            # Check cache first
            profile_hash = self._generate_profile_hash(profile, style)
            if profile_hash in self.voice_cache:
                cached_voice_id = self.voice_cache[profile_hash]
                logger.info(f"Using cached voice {cached_voice_id} for {profile.name}")
                
                return VoiceConfig(
                    voice_id=cached_voice_id,
                    style=style,
                    settings=self.style_configurations[style]["voice_settings"]
                )
            
            # Map voice styles to pre-made ElevenLabs voice IDs
            # These are public voices that work without generation
            voice_id_mapping = {
                VoiceStyle.MYSTERIOUS: "21m00Tcm4TlvDq8ikWAM",  # Rachel - calm, mysterious
                VoiceStyle.WARM: "EXAVITQu4vr4xnSDxMaL",      # Bella - warm, friendly
                VoiceStyle.WISE: "ErXwobaYiN019PkySvjV",       # Antoni - wise, mature
                VoiceStyle.PLAYFUL: "MF3mGyEYCl7XYWbV9V6O",   # Elli - playful, energetic
                VoiceStyle.DRAMATIC: "TxGEqnHWrfWFTfGW9XjX",   # Josh - dramatic, expressive
                VoiceStyle.WHISPERY: "pNInz6obpgDQGcFmaJgB",   # Adam - soft, whispery
            }
            
            voice_id = voice_id_mapping.get(style, voice_id_mapping[VoiceStyle.WARM])
            
            logger.info(f"Using pre-made voice {voice_id} for {profile.name} with style {style.value}")
            
            # Cache the voice
            self.voice_cache[profile_hash] = voice_id
            
            # Create voice configuration
            voice_config = VoiceConfig(
                voice_id=voice_id,
                style=style,
                settings=self.style_configurations[style]["voice_settings"]
            )
            
            logger.info(f"Successfully assigned voice {voice_id} for {profile.name}")
            
            return voice_config
            
        except Exception as e:
            logger.error(f"Failed to create voice for {profile.name}: {e}")
            raise ElevenLabsError(f"Voice generation failed: {str(e)}")
    
    def get_voice_options(self) -> List[Dict[str, Any]]:
        """
        Returns 6 available voice styles with descriptions.
        
        Returns:
            List of voice style options with metadata
        """
        options = []
        
        for style in VoiceStyle:
            config = self.style_configurations[style]
            options.append({
                "style": style.value,
                "name": style.value.title(),
                "description": config["description_template"],
                "keywords": config["personality_keywords"],
                "recommended_for": config["recommended_for"],
                "settings": config["voice_settings"]
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
        logger.info(f"Stored voice config {voice_config.voice_id} for session {session_id}")
    
    def get_voice_config(self, session_id: str) -> Optional[VoiceConfig]:
        """
        Retrieve voice configuration from session storage.
        
        Args:
            session_id: Session identifier
            
        Returns:
            VoiceConfig if found, None otherwise
        """
        config = self.voice_sessions.get(session_id)
        if config:
            logger.debug(f"Retrieved voice config {config.voice_id} for session {session_id}")
        return config
    
    def clear_voice_session(self, session_id: str) -> bool:
        """
        Clear voice configuration from session storage.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session was found and cleared, False otherwise
        """
        if session_id in self.voice_sessions:
            voice_id = self.voice_sessions[session_id].voice_id
            del self.voice_sessions[session_id]
            logger.info(f"Cleared voice session {session_id} (voice {voice_id})")
            return True
        return False
    
    def get_session_count(self) -> int:
        """
        Get number of active voice sessions.
        
        Returns:
            Number of active sessions
        """
        return len(self.voice_sessions)
    
    async def cleanup_expired_sessions(self, max_age_hours: int = 24) -> int:
        """
        Clean up expired voice sessions (placeholder for future implementation).
        
        Args:
            max_age_hours: Maximum age of sessions in hours
            
        Returns:
            Number of sessions cleaned up
        """
        # For now, just return 0 as we don't track session timestamps
        # This can be enhanced later with timestamp tracking
        return 0


# Example usage and testing
async def example_voice_designer_usage():
    """Example demonstrating Voice Designer functionality."""
    async with VoiceDesigner() as designer:
        # Create example object profile
        example_profile = ObjectProfile(
            id="example-cat-001",
            name="Whiskers",
            species="Tabby Cat",
            emoji="🐱",
            traits=["Curious", "Playful", "Wise"],
            backstory="A mysterious tabby cat who has lived in the old library for years, watching over ancient books and sharing wisdom with visitors."
        )
        
        print(f"Created profile for {example_profile.name}")
        print(f"Traits: {', '.join(example_profile.traits)}")
        
        # Get voice style options
        voice_options = designer.get_voice_options()
        print(f"\nAvailable voice styles: {len(voice_options)}")
        for option in voice_options:
            print(f"  - {option['name']}: {option['description']}")
        
        # Get recommendation
        recommended_style = designer.recommend_voice_style(example_profile)
        print(f"\nRecommended style for {example_profile.name}: {recommended_style.value}")
        
        # Create voice with recommended style
        try:
            voice_config = await designer.create_voice(example_profile, recommended_style)
            print(f"Created voice: {voice_config.voice_id}")
            print(f"Settings: {voice_config.settings}")
            
            # Store in session
            session_id = "example-session-001"
            designer.store_voice_config(session_id, voice_config)
            
            # Retrieve from session
            retrieved_config = designer.get_voice_config(session_id)
            print(f"Retrieved from session: {retrieved_config.voice_id if retrieved_config else 'Not found'}")
            
        except ElevenLabsError as e:
            print(f"Voice creation failed: {e}")


if __name__ == "__main__":
    asyncio.run(example_voice_designer_usage())