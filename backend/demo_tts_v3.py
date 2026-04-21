#!/usr/bin/env python3
"""
Demo script for ElevenLabs TTS v3 API integration with emotional tags.

This script demonstrates the key features implemented in task 3.4:
- Text-to-Speech v3 API integration
- Emotional tag detection based on conversation context
- Audio format conversion and streaming support
- Voice configuration with emotional adjustments

Usage:
    python demo_tts_v3.py
"""
import asyncio
import os
from src.services.elevenlabs_service import ElevenLabsService
from src.models import VoiceConfig, VoiceStyle


async def demo_emotional_tag_detection():
    """Demonstrate emotional tag detection from text and context."""
    print("=== Emotional Tag Detection Demo ===")
    
    # Create service with demo API key
    service = ElevenLabsService(api_key="demo_key_12345")
    
    # Test various emotional texts
    test_texts = [
        "I'm so excited to meet you!",
        "This is absolutely amazing and wonderful!",
        "I feel quite sad and disappointed today.",
        "I'm really angry about this situation!",
        "I'm shocked and astonished by this news!",
        "I wonder how this fascinating mechanism works?",
        "Everything is peaceful and calm here.",
        "There's something mysterious about this place.",
        "Let's have some fun and play together!",
        "With great wisdom comes deep understanding.",
        "The weather is nice today."  # Neutral text
    ]
    
    for text in test_texts:
        emotions = service._detect_emotional_tags(text)
        print(f"Text: '{text}'")
        print(f"Detected emotions: {emotions}")
        print()


async def demo_conversation_context_influence():
    """Demonstrate how conversation context influences emotional detection."""
    print("=== Conversation Context Influence Demo ===")
    
    service = ElevenLabsService(api_key="demo_key_12345")
    session_id = "demo_session"
    
    # Build up conversation context
    conversation_messages = [
        "Hi there! How are you doing?",
        "I'm having such a wonderful day!",
        "Everything is going amazingly well!",
        "I'm so excited about our conversation!"
    ]
    
    # Add messages to context
    for message in conversation_messages:
        service.add_conversation_message(session_id, message)
    
    # Test neutral text with emotional context
    neutral_text = "I see what you mean."
    context = service.get_conversation_context(session_id)
    emotions_with_context = service._detect_emotional_tags(neutral_text, context)
    emotions_without_context = service._detect_emotional_tags(neutral_text)
    
    print(f"Conversation context: {context}")
    print(f"Neutral text: '{neutral_text}'")
    print(f"Emotions without context: {emotions_without_context}")
    print(f"Emotions with context: {emotions_with_context}")
    print()


async def demo_audio_format_settings():
    """Demonstrate audio format settings for different output types."""
    print("=== Audio Format Settings Demo ===")
    
    service = ElevenLabsService(api_key="demo_key_12345")
    
    formats = ["mp3", "wav", "pcm", "unknown_format"]
    
    for format_type in formats:
        settings = service._get_audio_format_settings(format_type)
        print(f"Format: {format_type}")
        print(f"Settings: {settings}")
        print()


async def demo_voice_configuration_with_emotions():
    """Demonstrate voice configuration with emotional adjustments."""
    print("=== Voice Configuration with Emotions Demo ===")
    
    service = ElevenLabsService(api_key="demo_key_12345")
    
    # Create sample voice config
    voice_config = VoiceConfig(
        voice_id="demo_voice_123",
        style=VoiceStyle.PLAYFUL,
        settings={
            "stability": 0.6,
            "similarity_boost": 0.7,
            "style": 0.5
        }
    )
    
    # Test emotional adjustment logic
    emotional_texts = [
        ("I'm absolutely thrilled!", "excited"),
        ("I feel so sad today.", "sad"),
        ("This is really making me angry!", "angry"),
        ("Everything is calm and peaceful.", "calm")
    ]
    
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
    
    for text, expected_emotion in emotional_texts:
        emotions = service._detect_emotional_tags(text)
        original_style = voice_config.settings["style"]
        
        if emotions and emotions[0] in emotion_style_mapping:
            adjusted_style = emotion_style_mapping[emotions[0]]
        else:
            adjusted_style = original_style
        
        print(f"Text: '{text}'")
        print(f"Detected emotions: {emotions}")
        print(f"Original style: {original_style}")
        print(f"Adjusted style: {adjusted_style}")
        print()


async def demo_tts_v3_payload_structure():
    """Demonstrate TTS v3 payload structure without making API calls."""
    print("=== TTS v3 Payload Structure Demo ===")
    
    service = ElevenLabsService(api_key="demo_key_12345")
    
    # Sample parameters
    text = "Hello! I'm excited to talk with you!"
    voice_id = "demo_voice_123"
    voice_settings = {
        "stability": 0.6,
        "similarity_boost": 0.7,
        "style": 0.5
    }
    conversation_context = ["Hi there!", "How are you doing?"]
    
    # Demonstrate the payload construction logic
    emotional_tags = service._detect_emotional_tags(text, conversation_context)
    format_settings = service._get_audio_format_settings("mp3")
    
    # Simulate payload construction
    payload = {
        "text": text,
        "model_id": "eleven_turbo_v2_5",
        "voice_settings": voice_settings.copy(),
        "pronunciation_dictionary_locators": [],
        "seed": None,
        "previous_text": conversation_context[-1] if conversation_context else None,
        "next_text": None,
        "previous_request_ids": [],
        "response_format": format_settings["output_format"],
        "optimize_streaming_latency": format_settings["optimize_streaming_latency"],
        "output_format": format_settings["output_format"]
    }
    
    # Apply emotional adjustment
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
    
    if emotional_tags:
        primary_emotion = emotional_tags[0]
        if primary_emotion in emotion_style_mapping:
            payload["voice_settings"]["style"] = emotion_style_mapping[primary_emotion]
    
    print(f"Input text: '{text}'")
    print(f"Conversation context: {conversation_context}")
    print(f"Detected emotions: {emotional_tags}")
    print(f"TTS v3 Payload structure:")
    for key, value in payload.items():
        print(f"  {key}: {value}")
    print()


async def demo_session_management():
    """Demonstrate session management for voice configs and conversation context."""
    print("=== Session Management Demo ===")
    
    service = ElevenLabsService(api_key="demo_key_12345")
    
    # Voice session management
    voice_config = VoiceConfig(
        voice_id="demo_voice_456",
        style=VoiceStyle.MYSTERIOUS,
        settings={
            "stability": 0.7,
            "similarity_boost": 0.6,
            "style": 0.4
        }
    )
    
    session_id = "demo_session_123"
    
    # Store and retrieve voice config
    service.store_voice_config(session_id, voice_config)
    retrieved_config = service.get_voice_config(session_id)
    
    print(f"Stored voice config for session: {session_id}")
    print(f"Retrieved config: {retrieved_config.model_dump() if retrieved_config else None}")
    
    # Conversation context management
    messages = [
        "Hello, mysterious entity!",
        "What secrets do you hold?",
        "I'm curious about your origins.",
        "Tell me something enigmatic."
    ]
    
    for message in messages:
        service.add_conversation_message(session_id, message)
    
    context = service.get_conversation_context(session_id)
    print(f"Conversation context: {context}")
    
    # Clear session
    service.clear_voice_session(session_id)
    service.clear_conversation_context(session_id)
    print("Session cleared successfully")
    print()


async def main():
    """Run all demo functions."""
    print("ElevenLabs TTS v3 API Integration Demo")
    print("=" * 50)
    print()
    
    await demo_emotional_tag_detection()
    await demo_conversation_context_influence()
    await demo_audio_format_settings()
    await demo_voice_configuration_with_emotions()
    await demo_tts_v3_payload_structure()
    await demo_session_management()
    
    print("Demo completed successfully!")
    print()
    print("Key Features Implemented:")
    print("✓ Emotional tag detection from text content")
    print("✓ Conversation context influence on emotions")
    print("✓ Audio format conversion and streaming support")
    print("✓ Voice style adjustment based on emotions")
    print("✓ TTS v3 API payload construction")
    print("✓ Session management for voice configs and context")
    print("✓ /api/speak endpoint for text-to-speech conversion")


if __name__ == "__main__":
    asyncio.run(main())