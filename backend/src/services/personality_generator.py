"""
Personality generation service for creating character profiles.

This module generates unique character names, personality traits,
and backstories for identified objects.

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5
"""
import logging
import random
import uuid
from typing import List, Dict, Any

from ..models import ObjectIdentification, ObjectProfile
from ..exceptions import ValidationError

logger = logging.getLogger(__name__)


class PersonalityGenerator:
    """
    Service for generating character personalities from object identification.
    
    Handles:
    - Unique name generation
    - Exactly 3 personality trait creation
    - Engaging backstory generation
    """
    
    def __init__(self):
        """Initialize personality generator with trait and name databases."""
        # Name prefixes and suffixes for generation
        self.name_prefixes = {
            "cat": ["Whiskers", "Shadow", "Luna", "Felix", "Mittens"],
            "dog": ["Buddy", "Max", "Bella", "Charlie", "Cooper"],
            "bird": ["Tweety", "Chirpy", "Feather", "Sky", "Wing"],
            "flower": ["Rose", "Lily", "Daisy", "Violet", "Bloom"],
            "tree": ["Oak", "Willow", "Cedar", "Maple", "Pine"],
            "book": ["Sage", "Story", "Page", "Tome", "Chronicle"],
            "default": ["Spirit", "Soul", "Essence", "Being", "Entity"]
        }
        
        # Personality trait database
        self.trait_categories = {
            "positive": ["Friendly", "Curious", "Wise", "Playful", "Gentle", "Brave", "Creative", "Patient"],
            "energetic": ["Energetic", "Lively", "Adventurous", "Bold", "Dynamic", "Spirited"],
            "calm": ["Calm", "Peaceful", "Serene", "Thoughtful", "Contemplative", "Tranquil"],
            "mysterious": ["Mysterious", "Enigmatic", "Secretive", "Mystical", "Ancient"],
            "social": ["Cheerful", "Caring", "Protective", "Loyal", "Devoted", "Nurturing"]
        }
        
        # Emoji mappings
        self.emoji_map = {
            "cat": "🐱", "dog": "🐕", "bird": "🐦", "fish": "🐠",
            "flower": "🌸", "tree": "🌳", "book": "📚", "music": "🎵",
            "star": "⭐", "moon": "🌙", "sun": "☀️", "cloud": "☁️",
            "default": "✨"
        }
    
    def generate_name(self, identification: ObjectIdentification) -> str:
        """
        Generate unique character name based on object type.
        
        Args:
            identification: Object identification data
            
        Returns:
            Generated character name
        """
        object_type = identification.object_type.lower()
        
        # Find matching name category
        for category, names in self.name_prefixes.items():
            if category in object_type:
                return random.choice(names)
        
        # Use default names
        return random.choice(self.name_prefixes["default"])
    
    def generate_traits(
        self,
        identification: ObjectIdentification
    ) -> List[str]:
        """
        Generate exactly 3 personality traits.
        
        Args:
            identification: Object identification data
            
        Returns:
            List of exactly 3 personality traits
        """
        traits = []
        characteristics = [c.lower() for c in identification.characteristics]
        
        # Map characteristics to trait categories
        if any(word in " ".join(characteristics) for word in ["playful", "fun", "energetic"]):
            traits.append(random.choice(self.trait_categories["energetic"]))
        
        if any(word in " ".join(characteristics) for word in ["calm", "peaceful", "quiet"]):
            traits.append(random.choice(self.trait_categories["calm"]))
        
        if any(word in " ".join(characteristics) for word in ["mysterious", "dark", "ancient"]):
            traits.append(random.choice(self.trait_categories["mysterious"]))
        
        # Fill remaining slots with positive traits
        while len(traits) < 3:
            trait = random.choice(self.trait_categories["positive"])
            if trait not in traits:
                traits.append(trait)
        
        return traits[:3]
    
    def generate_backstory(
        self,
        name: str,
        identification: ObjectIdentification,
        traits: List[str]
    ) -> str:
        """
        Generate engaging backstory paragraph.
        
        Args:
            name: Character name
            identification: Object identification
            traits: Personality traits
            
        Returns:
            Backstory paragraph
        """
        object_type = identification.object_type
        species = identification.species or object_type
        
        # Create backstory templates
        templates = [
            f"{name} is a {traits[0].lower()} {species} who has seen many adventures. "
            f"With a {traits[1].lower()} spirit and {traits[2].lower()} nature, "
            f"{name} brings joy to everyone who encounters this special {object_type}.",
            
            f"Meet {name}, a remarkable {species} with a {traits[0].lower()} personality. "
            f"Known for being {traits[1].lower()} and {traits[2].lower()}, "
            f"{name} has a unique story to share with the world.",
            
            f"In a world full of ordinary things, {name} stands out as an extraordinary {species}. "
            f"This {traits[0].lower()} and {traits[1].lower()} {object_type} "
            f"embodies the essence of being {traits[2].lower()}."
        ]
        
        return random.choice(templates)
    
    def get_emoji(self, identification: ObjectIdentification) -> str:
        """
        Get representative emoji for object type.
        
        Args:
            identification: Object identification
            
        Returns:
            Emoji character
        """
        object_type = identification.object_type.lower()
        
        for key, emoji in self.emoji_map.items():
            if key in object_type:
                return emoji
        
        return self.emoji_map["default"]
    
    def generate_profile(
        self,
        identification: ObjectIdentification
    ) -> ObjectProfile:
        """
        Generate complete object profile.
        
        Args:
            identification: Object identification data
            
        Returns:
            Complete ObjectProfile
            
        Raises:
            ValidationError: If profile generation fails
        """
        try:
            # Generate all components
            name = self.generate_name(identification)
            traits = self.generate_traits(identification)
            emoji = self.get_emoji(identification)
            backstory = self.generate_backstory(name, identification, traits)
            
            # Create profile
            profile = ObjectProfile(
                id=f"profile_{uuid.uuid4().hex[:12]}",
                name=name,
                species=identification.species or identification.object_type,
                emoji=emoji,
                traits=traits,
                backstory=backstory
            )
            
            logger.info(f"Generated profile for {name} ({profile.species})")
            
            return profile
            
        except Exception as e:
            logger.error(f"Failed to generate profile: {e}")
            raise ValidationError(f"Profile generation failed: {str(e)}")


# Example usage
def example_personality_generation():
    """Example of how to use the Personality Generator."""
    # Create example identification
    identification = ObjectIdentification(
        object_type="cat",
        species="tabby cat",
        characteristics=["fluffy", "orange", "playful"],
        confidence=0.95
    )
    
    generator = PersonalityGenerator()
    profile = generator.generate_profile(identification)
    
    print(f"Name: {profile.name} {profile.emoji}")
    print(f"Species: {profile.species}")
    print(f"Traits: {', '.join(profile.traits)}")
    print(f"Backstory: {profile.backstory}")


if __name__ == "__main__":
    example_personality_generation()
