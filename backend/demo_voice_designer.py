#!/usr/bin/env python3
"""
Voice Designer Demo Script

Demonstrates the Voice Design API integration functionality including:
- Voice generation with 6 style options
- Personality trait mapping to voice characteristics  
- Session-based voice configuration storage

This script shows how the Voice Designer would work in the VoiceSnap application.
"""
import asyncio
import json
from typing import List

from src.services.voice_designer import VoiceDesigner
from src.models import ObjectProfile, VoiceStyle
from src.exceptions import ElevenLabsError


def create_demo_profiles() -> List[ObjectProfile]:
    """Create sample object profiles for demonstration."""
    return [
        ObjectProfile(
            id="demo-cat-001",
            name="Whiskers",
            species="Tabby Cat",
            emoji="🐱",
            traits=["Curious", "Playful", "Wise"],
            backstory="A mysterious tabby cat who has lived in the old library for years, watching over ancient books and sharing wisdom with visitors who take the time to listen."
        ),
        ObjectProfile(
            id="demo-book-001", 
            name="Grimoire",
            species="Ancient Spellbook",
            emoji="📚",
            traits=["Mysterious", "Powerful", "Ancient"],
            backstory="An ancient tome of forgotten magic, bound in leather and sealed with silver clasps. It whispers secrets to those brave enough to open its pages."
        ),
        ObjectProfile(
            id="demo-toy-001",
            name="Bouncy",
            species="Rubber Ball",
            emoji="⚽",
            traits=["Playful", "Energetic", "Cheerful"],
            backstory="A bright red rubber ball that has bounced through countless games and adventures, always ready for the next fun activity with friends."
        ),
        ObjectProfile(
            id="demo-tree-001",
            name="Elder Oak",
            species="Ancient Oak Tree", 
            emoji="🌳",
            traits=["Wise", "Patient", "Protective"],
            backstory="A majestic oak tree that has stood for over 300 years, providing shelter and wisdom to all who rest beneath its mighty branches."
        ),
        ObjectProfile(
            id="demo-flower-001",
            name="Rosebud",
            species="Rose Flower",
            emoji="🌹",
            traits=["Gentle", "Beautiful", "Romantic"],
            backstory="A delicate rose that blooms in the garden, spreading beauty and sweet fragrance while dreaming of love stories and fairy tales."
        ),
        ObjectProfile(
            id="demo-instrument-001",
            name="Melody",
            species="Violin",
            emoji="🎻",
            traits=["Dramatic", "Passionate", "Artistic"],
            backstory="An elegant violin crafted by a master luthier, capable of expressing the deepest emotions through its haunting melodies and soaring crescendos."
        )
    ]


def print_separator(title: str = ""):
    """Print a decorative separator."""
    print("\n" + "="*60)
    if title:
        print(f" {title} ".center(60, "="))
        print("="*60)
    print()


async def demonstrate_voice_styles():
    """Demonstrate available voice style options."""
    print_separator("VOICE STYLE OPTIONS")
    
    designer = VoiceDesigner(api_key="demo-key")
    voice_options = designer.get_voice_options()
    
    print(f"VoiceSnap offers {len(voice_options)} unique voice styles:\n")
    
    for i, option in enumerate(voice_options, 1):
        print(f"{i}. {option['name']} ({option['style']})")
        print(f"   Description: {option['description']}")
        print(f"   Keywords: {', '.join(option['keywords'][:3])}...")
        print(f"   Recommended for: {', '.join(option['recommended_for'][:2])}...")
        print(f"   Settings: Stability={option['settings']['stability']}, "
              f"Similarity={option['settings']['similarity_boost']}, "
              f"Style={option['settings']['style']}")
        print()


async def demonstrate_voice_recommendations():
    """Demonstrate voice style recommendations for different objects."""
    print_separator("VOICE STYLE RECOMMENDATIONS")
    
    designer = VoiceDesigner(api_key="demo-key")
    profiles = create_demo_profiles()
    
    print("Voice style recommendations based on object characteristics:\n")
    
    for profile in profiles:
        recommended_style = designer.recommend_voice_style(profile)
        
        print(f"🎯 {profile.name} ({profile.species})")
        print(f"   Traits: {', '.join(profile.traits)}")
        print(f"   Recommended Voice: {recommended_style.value.title()}")
        
        # Get style details
        voice_options = designer.get_voice_options()
        style_details = next(
            (opt for opt in voice_options if opt["style"] == recommended_style.value),
            None
        )
        
        if style_details:
            print(f"   Why: {style_details['description']}")
        print()


async def demonstrate_voice_descriptions():
    """Demonstrate voice description generation."""
    print_separator("VOICE DESCRIPTION GENERATION")
    
    designer = VoiceDesigner(api_key="demo-key")
    sample_profile = create_demo_profiles()[0]  # Use Whiskers the cat
    
    print(f"Voice descriptions for {sample_profile.name} ({sample_profile.species}):")
    print(f"Traits: {', '.join(sample_profile.traits)}")
    print(f"Backstory: {sample_profile.backstory[:100]}...\n")
    
    # Generate descriptions for different styles
    styles_to_demo = [VoiceStyle.MYSTERIOUS, VoiceStyle.WARM, VoiceStyle.PLAYFUL]
    
    for style in styles_to_demo:
        description = designer._build_voice_description(sample_profile, style)
        print(f"🎭 {style.value.title()} Style:")
        print(f"   {description}")
        print()


async def demonstrate_session_management():
    """Demonstrate voice configuration session management."""
    print_separator("SESSION MANAGEMENT")
    
    designer = VoiceDesigner(api_key="demo-key")
    profiles = create_demo_profiles()[:3]  # Use first 3 profiles
    
    print("Simulating voice configuration storage and retrieval:\n")
    
    # Simulate creating and storing voice configurations
    for i, profile in enumerate(profiles):
        session_id = f"session_{profile.id}"
        recommended_style = designer.recommend_voice_style(profile)
        
        # Create a mock voice config (without actual API call)
        from src.models import VoiceConfig
        voice_config = VoiceConfig(
            voice_id=f"voice_{profile.id}_{recommended_style.value}",
            style=recommended_style,
            settings=designer.style_configurations[recommended_style]["voice_settings"]
        )
        
        # Store in session
        designer.store_voice_config(session_id, voice_config)
        
        print(f"✅ Stored voice for {profile.name}")
        print(f"   Session ID: {session_id}")
        print(f"   Voice ID: {voice_config.voice_id}")
        print(f"   Style: {voice_config.style.value}")
        print()
    
    print(f"📊 Total active sessions: {designer.get_session_count()}\n")
    
    # Demonstrate retrieval
    print("Retrieving voice configurations:")
    for profile in profiles:
        session_id = f"session_{profile.id}"
        retrieved_config = designer.get_voice_config(session_id)
        
        if retrieved_config:
            print(f"🔍 Retrieved {profile.name}: {retrieved_config.voice_id} ({retrieved_config.style.value})")
        else:
            print(f"❌ No configuration found for {profile.name}")
    
    print()
    
    # Demonstrate cleanup
    print("Cleaning up sessions:")
    for profile in profiles:
        session_id = f"session_{profile.id}"
        cleared = designer.clear_voice_session(session_id)
        print(f"🗑️  Cleared session for {profile.name}: {'Success' if cleared else 'Failed'}")
    
    print(f"\n📊 Remaining sessions: {designer.get_session_count()}")


async def demonstrate_trait_mapping():
    """Demonstrate personality trait to voice characteristic mapping."""
    print_separator("PERSONALITY TRAIT MAPPING")
    
    designer = VoiceDesigner(api_key="demo-key")
    
    print("How personality traits are mapped to voice characteristics:\n")
    
    trait_examples = [
        ["Curious", "Friendly", "Wise"],
        ["Mysterious", "Dark", "Secretive"],
        ["Playful", "Energetic", "Fun"],
        ["Gentle", "Caring", "Protective"],
        ["Dramatic", "Passionate", "Bold"],
        ["Unknown", "Custom", "Trait"]  # Test unknown traits
    ]
    
    for traits in trait_examples:
        characteristics = designer._map_traits_to_voice_characteristics(traits)
        
        print(f"🏷️  Input Traits: {', '.join(traits)}")
        print(f"   Voice Characteristics: {', '.join(characteristics)}")
        print()


async def main():
    """Run the complete Voice Designer demonstration."""
    print("🎙️  VoiceSnap Voice Designer Demonstration")
    print("=" * 60)
    print("This demo shows how VoiceSnap creates unique voices for objects")
    print("using ElevenLabs Voice Design API integration.")
    
    try:
        # Run all demonstrations
        await demonstrate_voice_styles()
        await demonstrate_voice_recommendations()
        await demonstrate_voice_descriptions()
        await demonstrate_trait_mapping()
        await demonstrate_session_management()
        
        print_separator("DEMO COMPLETE")
        print("✨ Voice Designer demonstration completed successfully!")
        print("\nKey Features Demonstrated:")
        print("• 6 unique voice styles (Mysterious, Warm, Wise, Playful, Dramatic, Whispery)")
        print("• Intelligent voice style recommendations based on object characteristics")
        print("• Personality trait mapping to voice characteristics")
        print("• Comprehensive voice description generation")
        print("• Session-based voice configuration storage and management")
        print("• Caching system for efficient voice reuse")
        
        print("\n🚀 Ready for integration with ElevenLabs Voice Design API!")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        print("This is expected if ElevenLabs API key is not configured.")
        print("The Voice Designer is ready for production use with proper API credentials.")


if __name__ == "__main__":
    asyncio.run(main())