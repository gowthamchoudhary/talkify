"""
Talkify FastAPI Application
Main application entry point with middleware, dependencies, and core endpoints.
"""
import os
import time
import uuid
import logging
import tempfile
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, FileResponse

from src.config import settings
from src.dependencies import (
    get_settings, 
    get_http_session, 
    http_client_manager,
    get_elevenlabs_config,
    get_gemini_config
)
from src.models import (
    ObjectProfile, VoiceStyle, APIResponse, SpeakRequest, AmbientRequest,
    ProfileRequest, SingRequest, ObjectIdentification
)
from src.services.voice_designer import VoiceDesigner
from src.services.elevenlabs_service import ElevenLabsService
from src.services.gemini_vision import GeminiVisionService
from src.services.groq_vision import GroqVisionService
from src.services.personality_generator import PersonalityGenerator
from src.services.sound_effects import SoundEffectsService
from src.services.music_generator import MusicGeneratorService
from src.exceptions import ElevenLabsError, GeminiError, ValidationError
from src.websocket_handler import websocket_manager
from src.validation import validate_image_file
from fastapi import UploadFile, File

# Configure logging
logger = logging.getLogger(__name__)

# In-memory map of session audio files
_audio_files: Dict[str, str] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    print(f"Starting Talkify API in {settings.environment} mode")
    
    yield
    
    # Shutdown
    print("Shutting down Talkify API")
    await http_client_manager.close()


# FastAPI application with lifespan management
app = FastAPI(
    title="Talkify API",
    description="Backend API for Talkify - Bring objects to life with AI personalities and voices",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# Security middleware - only allow specific hosts in production
if settings.environment == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["talkify-api.onrender.com", "*.onrender.com"]
    )

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request, call_next):
    """Add processing time header to all responses."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred"
            },
            "timestamp": time.time()
        }
    )


@app.get("/health")
async def health_check(
    settings_dep = Depends(get_settings),
    elevenlabs_config = Depends(get_elevenlabs_config),
    gemini_config = Depends(get_gemini_config)
) -> Dict[str, Any]:
    """
    Comprehensive health check endpoint.
    
    Validates:
    - Service availability
    - Configuration completeness
    - API key presence (without exposing values)
    - Environment settings
    """
    health_status = {
        "status": "healthy",
        "service": "talkify-api",
        "version": "1.0.0",
        "environment": settings_dep.environment,
        "timestamp": time.time(),
        "checks": {
            "configuration": "ok",
            "elevenlabs_api_key": "configured" if elevenlabs_config["api_key"] else "missing",
            "gemini_api_key": "configured" if gemini_config["api_key"] else "missing",
            "cors_origins": len(settings_dep.cors_origins),
            "max_file_size": f"{settings_dep.max_file_size / (1024*1024):.1f}MB"
        }
    }
    
    # Check if critical configuration is missing
    if not elevenlabs_config["api_key"] or not gemini_config["api_key"]:
        health_status["status"] = "degraded"
        health_status["checks"]["warning"] = "Missing required API keys"
    
    return health_status


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint with basic API information."""
    return {
        "message": "Talkify API is running",
        "version": "1.0.0",
        "docs": "/docs" if settings.debug else "Documentation disabled in production"
    }


@app.get("/api/config")
async def get_public_config(settings_dep = Depends(get_settings)) -> Dict[str, Any]:
    """
    Get public configuration information for frontend.
    Does not expose sensitive data like API keys.
    """
    return {
        "max_file_size": settings_dep.max_file_size,
        "allowed_image_types": settings_dep.allowed_image_types,
        "session_timeout": settings_dep.session_timeout,
        "environment": settings_dep.environment
    }


@app.get("/api/voice/styles")
async def get_voice_styles() -> APIResponse:
    """
    Get available voice style options.
    
    Returns:
        List of 6 voice styles with descriptions and characteristics
    """
    try:
        async with VoiceDesigner() as designer:
            voice_options = designer.get_voice_options()
            
        return APIResponse(
            success=True,
            data={"voice_styles": voice_options}
        )
    except Exception as e:
        return APIResponse(
            success=False,
            error={"code": "VOICE_STYLES_ERROR", "message": str(e)}
        )


@app.post("/api/voice/create")
async def create_voice_design(
    profile: ObjectProfile,
    style: VoiceStyle = None
) -> APIResponse:
    """
    Create a unique voice design for an object profile.
    
    Args:
        profile: Object character profile
        style: Optional voice style (if not provided, will be recommended)
        
    Returns:
        Voice configuration with generated voice ID and settings
    """
    try:
        async with VoiceDesigner() as designer:
            # Use recommended style if none provided
            if style is None:
                style = designer.recommend_voice_style(profile)
            
            # Create the voice
            voice_config = await designer.create_voice(profile, style)
            
            # Store in session (using profile ID as session ID for demo)
            session_id = f"session_{profile.id}"
            designer.store_voice_config(session_id, voice_config)
            
            return APIResponse(
                success=True,
                data={
                    "voice_config": voice_config.model_dump(),
                    "session_id": session_id,
                    "recommended_style": style.value
                }
            )
        
    except ElevenLabsError as e:
        return APIResponse(
            success=False,
            error={"code": "VOICE_CREATION_ERROR", "message": str(e)}
        )
    except Exception as e:
        return APIResponse(
            success=False,
            error={"code": "INTERNAL_ERROR", "message": str(e)}
        )


@app.get("/api/voice/recommend/{object_type}")
async def recommend_voice_style(object_type: str, traits: str = "") -> APIResponse:
    """
    Get voice style recommendation for an object type and traits.
    
    Args:
        object_type: Type of object (e.g., "cat", "book", "toy")
        traits: Comma-separated personality traits
        
    Returns:
        Recommended voice style with explanation
    """
    try:
        # Create a minimal profile for recommendation
        trait_list = [trait.strip() for trait in traits.split(",") if trait.strip()]
        if not trait_list:
            trait_list = ["Friendly", "Curious", "Gentle"]  # Default traits
        
        temp_profile = ObjectProfile(
            id="temp",
            name="TempObject",
            species=object_type,
            emoji="🔮",
            traits=trait_list[:3],  # Ensure exactly 3 traits
            backstory="A temporary profile for voice recommendation."
        )
        
        async with VoiceDesigner() as designer:
            recommended_style = designer.recommend_voice_style(temp_profile)
            voice_options = designer.get_voice_options()
            
            # Find the recommended style details
            style_details = next(
                (opt for opt in voice_options if opt["style"] == recommended_style.value),
                None
            )
        
            return APIResponse(
                success=True,
                data={
                    "recommended_style": recommended_style.value,
                    "style_details": style_details,
                    "object_type": object_type,
                    "traits": trait_list
                }
            )
        
    except Exception as e:
        return APIResponse(
            success=False,
            error={"code": "RECOMMENDATION_ERROR", "message": str(e)}
        )


@app.post("/api/speak")
async def text_to_speech_endpoint(request: SpeakRequest) -> APIResponse:
    """
    Convert text to speech using ElevenLabs TTS API.
    
    Args:
        request: SpeakRequest containing text and voice configuration
        
    Returns:
        Audio URL and metadata for playback
    """
    try:
        # Use simple ElevenLabs client
        from src.services.elevenlabs_simple import SimpleElevenLabsClient
        from src.config import settings
        
        async with SimpleElevenLabsClient(api_key=settings.elevenlabs_api_key) as client:
            # Convert text to speech
            audio_data = await client.text_to_speech(
                text=request.text,
                voice_id=request.voice_config.voice_id,
                voice_settings=request.voice_config.settings
            )
            
            # Generate session ID and save audio file
            session_id = f"tts_session_{int(time.time())}"
            audio_filename = f"{session_id}.mp3"
            audio_path = Path("audio_files") / audio_filename
            
            # Create audio directory if it doesn't exist
            audio_path.parent.mkdir(exist_ok=True)
            
            # Save audio data to file
            with open(audio_path, "wb") as f:
                f.write(audio_data)
            
            # Store in memory map for serving
            _audio_files[session_id] = str(audio_path)
            
            audio_url = f"/api/audio/{audio_filename}"
            
            return APIResponse(
                success=True,
                data={
                    "audio_url": audio_url,
                    "session_id": session_id,
                    "text": request.text,
                    "voice_id": request.voice_config.voice_id,
                    "audio_format": "mp3",
                    "audio_size_bytes": len(audio_data),
                    "duration_estimate": len(request.text) * 0.1,  # Rough estimate: 0.1s per character
                    "voice_style": request.voice_config.style.value if hasattr(request.voice_config, 'style') else "default"
                }
            )
        
    except Exception as e:
        logger.error(f"TTS failed: {e}")
        return APIResponse(
            success=False,
            error={"code": "TTS_ERROR", "message": str(e)}
        )


@app.post("/api/ambient")
async def generate_ambient_endpoint(request: AmbientRequest) -> APIResponse:
    """
    Generate ambient sound effects for object type.
    
    Args:
        request: AmbientRequest with object type and intensity
        
    Returns:
        Ambient audio URL
    """
    try:
        async with SoundEffectsService() as service:
            audio_data = await service.generate_ambient_sound(
                object_type=request.object_type,
                duration=30.0,
                intensity=request.intensity
            )
        
        # Save audio to temp file
        audio_id = uuid.uuid4().hex[:12]
        tmp_path = Path(tempfile.gettempdir()) / f"ambient_{audio_id}.mp3"
        tmp_path.write_bytes(audio_data)
        _audio_files[audio_id] = str(tmp_path)
        
        return APIResponse(
            success=True,
            data={
                "audio_url": f"/api/audio/{audio_id}",
                "object_type": request.object_type,
                "duration": 30.0,
            }
        )
        
    except ElevenLabsError as e:
        return APIResponse(
            success=False,
            error={"code": "AMBIENT_ERROR", "message": str(e)}
        )
    except Exception as e:
        return APIResponse(
            success=False,
            error={"code": "INTERNAL_ERROR", "message": str(e)}
        )


@app.get("/api/audio/{audio_id}")
async def serve_audio(audio_id: str):
    """Serve generated audio files."""
    # Handle both song_id.mp3 and song_id formats
    clean_id = audio_id.replace('.mp3', '')
    
    # Check if file exists in memory map
    path = _audio_files.get(clean_id)
    if path and Path(path).exists():
        return FileResponse(
            path, 
            media_type="audio/mpeg",
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET",
                "Access-Control-Allow-Headers": "*",
                "Cache-Control": "public, max-age=3600"
            }
        )
    
    # Also check direct file path
    audio_path = Path("audio_files") / audio_id
    if audio_path.exists():
        return FileResponse(
            str(audio_path), 
            media_type="audio/mpeg",
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET", 
                "Access-Control-Allow-Headers": "*",
                "Cache-Control": "public, max-age=3600"
            }
        )
    
    raise HTTPException(status_code=404, detail="Audio file not found")


@app.get("/api/ambient/types")
async def get_available_ambient_types() -> APIResponse:
    """
    Get list of available ambient sound types with descriptions.
    
    Returns:
        List of supported object types for ambient sound generation
        
    Requirements: 6.1, 6.2
    """
    try:
        async with ElevenLabsService() as service:
            available_types = await service.get_available_ambient_types()
            
            return APIResponse(
                success=True,
                data={
                    "available_types": available_types,
                    "total_count": len(available_types),
                    "supported_formats": ["mp3", "wav"],
                    "intensity_range": {"min": 0.0, "max": 1.0},
                    "default_duration": 60,
                    "volume_mixing": "Automatic volume mixing ensures compatibility with speech"
                }
            )
        
    except Exception as e:
        return APIResponse(
            success=False,
            error={"code": "AMBIENT_TYPES_ERROR", "message": str(e)}
        )


@app.post("/api/ambient/contextual")
async def generate_contextual_ambient(
    object_type: str,
    conversation_active: bool = False,
    intensity: float = 0.3,
    duration_seconds: int = 60
) -> APIResponse:
    """
    Generate contextual ambient sound mix that adapts to conversation state.
    
    Args:
        object_type: Type of object for contextual sounds
        conversation_active: Whether a conversation is currently active
        intensity: Base intensity level (0.0 to 1.0)
        duration_seconds: Duration of the ambient mix
        
    Returns:
        Contextual ambient audio optimized for current state
        
    Requirements: 6.1, 6.2, 6.4, 6.5
    """
    try:
        async with ElevenLabsService() as service:
            # Generate contextual ambient mix
            ambient_audio = await service.create_contextual_ambient_mix(
                object_type=object_type,
                conversation_active=conversation_active,
                intensity=intensity,
                duration_seconds=duration_seconds
            )
            
            # Generate session ID
            context_session_id = f"contextual_{object_type}_{int(time.time())}"
            
            # Calculate adjusted intensity
            adjusted_intensity = intensity * 0.6 if conversation_active else intensity
            
            # In production, save to file storage
            contextual_url = f"/api/audio/contextual/{context_session_id}.mp3"
            
            return APIResponse(
                success=True,
                data={
                    "ambient_url": contextual_url,
                    "session_id": context_session_id,
                    "object_type": object_type,
                    "conversation_active": conversation_active,
                    "requested_intensity": intensity,
                    "adjusted_intensity": adjusted_intensity,
                    "duration_seconds": duration_seconds,
                    "audio_format": "mp3",
                    "audio_size_bytes": len(ambient_audio),
                    "optimization": "conversation" if conversation_active else "standalone",
                    "volume_mixed": True,
                    "speech_compatible": True
                }
            )
        
    except ElevenLabsError as e:
        return APIResponse(
            success=False,
            error={"code": "CONTEXTUAL_AMBIENT_ERROR", "message": str(e)}
        )
    except Exception as e:
        return APIResponse(
            success=False,
            error={"code": "INTERNAL_ERROR", "message": str(e)}
        )


@app.get("/api/scribe-token")
async def get_scribe_token():
    """
    Generate a single-use token for ElevenLabs speech-to-text.
    This token is used by the frontend for secure microphone access.
    """
    try:
        from src.services.elevenlabs_simple import SimpleElevenLabsClient
        from src.config import settings
        
        async with SimpleElevenLabsClient(api_key=settings.elevenlabs_api_key) as client:
            # Create single-use token for realtime scribe
            url = f"{client.base_url}/tokens/single-use"
            headers = {
                "xi-api-key": client.api_key,
                "Content-Type": "application/json"
            }
            payload = {
                "purpose": "realtime_scribe"
            }
            
            async with client.session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    token_data = await response.json()
                    return APIResponse(
                        success=True,
                        data=token_data
                    )
                else:
                    error_text = await response.text()
                    logger.error(f"Token generation failed: {error_text}")
                    return APIResponse(
                        success=False,
                        error={"code": "TOKEN_ERROR", "message": "Failed to generate token"}
                    )
    except Exception as e:
        logger.error(f"Token generation error: {e}")
        return APIResponse(
            success=False,
            error={"code": "INTERNAL_ERROR", "message": str(e)}
        )


async def generate_personality_response(user_text: str, profile_data: Dict[str, Any]) -> str:
    """Generate a personality-driven response to user input."""
    name = profile_data.get("name", "Object")
    traits = profile_data.get("traits", [])
    backstory = profile_data.get("backstory", "")
    species = profile_data.get("species", "object")
    
    # Simple personality-based responses
    trait_str = ", ".join(traits[:2]) if traits else "friendly"
    
    responses = [
        f"As a {trait_str} {species}, I think {user_text.lower()} is quite interesting!",
        f"You know, being {name} means I see things differently. About {user_text.lower()} - {backstory[:50]}...",
        f"That's fascinating! As a {species} with {trait_str} personality, I'd say {user_text.lower()} reminds me of my own experiences.",
        f"Oh, {user_text.lower()}? That's something I, {name}, can definitely relate to! {backstory[:30]}...",
        f"Interesting perspective! Being {trait_str}, I find {user_text.lower()} quite thought-provoking."
    ]
    
    import random
    return random.choice(responses)


@app.websocket("/ws/conversation")
async def websocket_conversation_endpoint(websocket: WebSocket):
    """
    Simple WebSocket endpoint for real-time conversation.
    """
    await websocket.accept()
    logger.info("WebSocket conversation connected")
    
    try:
        # Wait for initial message with profile data
        while True:
            try:
                message = await websocket.receive_json()
                
                if message.get("type") == "init":
                    profile_data = message.get("profile")
                    if not profile_data:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Profile data required"
                        })
                        continue
                    
                    # Send welcome message
                    await websocket.send_json({
                        "type": "message",
                        "from": "obj",
                        "text": f"Hello! I'm {profile_data['name']}, {profile_data.get('species', 'an object')}. {profile_data.get('backstory', 'Nice to meet you!')}",
                        "timestamp": int(time.time() * 1000)
                    })
                    
                elif message.get("type") == "message":
                    user_text = message.get("text", "").strip()
                    if not user_text:
                        continue
                    
                    # Get profile from previous init (simple approach)
                    profile_data = message.get("profile", {})
                    
                    # Generate AI response
                    response_text = await generate_personality_response(user_text, profile_data)
                    
                    # Generate TTS audio
                    voice_id = profile_data.get("voice_config", {}).get("voice_id", "21m00Tcm4TlvDq8ikWAM")
                    
                    from src.services.elevenlabs_simple import SimpleElevenLabsClient
                    async with SimpleElevenLabsClient(api_key=settings.elevenlabs_api_key) as client:
                        audio_data = await client.text_to_speech(
                            text=response_text,
                            voice_id=voice_id,
                            voice_settings={
                                "stability": 0.6,
                                "similarity_boost": 0.8,
                                "style": 0.7,
                                "use_speaker_boost": True
                            }
                        )
                        
                        # Save audio file
                        audio_id = f"conv_{int(time.time() * 1000)}"
                        audio_filename = f"{audio_id}.mp3"
                        audio_path = Path("audio_files") / audio_filename
                        audio_path.parent.mkdir(exist_ok=True)
                        
                        with open(audio_path, "wb") as f:
                            f.write(audio_data)
                        
                        _audio_files[audio_id] = str(audio_path)
                    
                    # Send response with audio
                    await websocket.send_json({
                        "type": "message",
                        "from": "obj",
                        "text": response_text,
                        "audio_url": f"/api/audio/{audio_filename}",
                        "timestamp": int(time.time() * 1000)
                    })
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
        
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")


async def generate_personality_response(user_text: str, profile_data: dict) -> str:
    """Generate a personality-driven response using the object's actual personality."""
    name = profile_data.get("name", "Object")
    traits = profile_data.get("traits", [])
    species = profile_data.get("species", "object")
    backstory = profile_data.get("backstory", "")
    emoji = profile_data.get("emoji", "")
    
    # Build personality context
    trait_str = ", ".join(traits) if traits else "friendly"
    
    # Create a personality-driven prompt
    personality_context = f"""You are {name}, a {species} {emoji}. 
Your personality traits are: {trait_str}.
Your backstory: {backstory}

Respond to the user's message in character, showing your unique personality.
Keep responses conversational, authentic, and under 50 words.
Show your traits through your words and tone."""

    user_input_lower = user_text.lower()
    
    # Handle common questions with personality
    if any(word in user_input_lower for word in ["hello", "hi", "hey"]):
        greetings = [
            f"Hey there! I'm {name}! {backstory[:80]}... What brings you here?",
            f"Hello! {emoji} I'm {name}, and I'm {trait_str}! Want to chat?",
            f"Hi! As a {species}, I'm always excited to meet someone new! I'm {name}."
        ]
        import random
        return random.choice(greetings)
    
    elif "how are you" in user_input_lower or "how're you" in user_input_lower:
        mood_responses = {
            "energetic": f"I'm bursting with energy! Being a {species} is amazing! How about you?",
            "playful": f"I'm feeling super playful today! Want to have some fun? 😄",
            "wise": f"I'm doing well, thank you. As a {species}, I find peace in reflection. And you?",
            "mysterious": f"I'm... intriguing, as always. There's much to discover about me. How are you?",
            "gentle": f"I'm doing wonderfully, thank you for asking. Your kindness warms my heart. 💕",
            "creative": f"I'm feeling inspired! My mind is full of creative ideas! How are you feeling?",
            "curious": f"I'm great! Always curious about everything around me. What about you?",
            "patient": f"I'm doing well, taking things one moment at a time. How are you today?"
        }
        for trait in traits:
            if trait.lower() in mood_responses:
                return mood_responses[trait.lower()]
        return f"I'm doing great! As {name} the {species}, life is always interesting! How about you?"
    
    elif "what are you" in user_input_lower or "who are you" in user_input_lower:
        return f"I'm {name}, a {trait_str} {species}! {backstory} What would you like to know about me?"
    
    elif "special" in user_input_lower or "unique" in user_input_lower:
        special_responses = {
            "energetic": f"What makes me special? My endless energy and enthusiasm! I bring excitement wherever I go!",
            "playful": f"I'm special because I make everything fun! Life's too short to be serious all the time! 🎉",
            "wise": f"My wisdom comes from experience. As a {species}, I've learned much about life and can share insights.",
            "mysterious": f"What makes me special? Ah, that's for you to discover... I hold many secrets.",
            "gentle": f"I'm special because I care deeply. My gentle nature helps others feel safe and understood.",
            "creative": f"My creativity! I see the world differently and can imagine endless possibilities!",
            "curious": f"My curiosity! I'm always asking questions and learning new things about the world!",
            "patient": f"My patience. I take time to understand things deeply and never rush important moments."
        }
        for trait in traits:
            if trait.lower() in special_responses:
                return special_responses[trait.lower()]
        return f"What makes me special? I'm {name}, a unique {species} with {trait_str} personality! {backstory[:60]}..."
    
    elif any(word in user_input_lower for word in ["can't hear", "no sound", "audio", "voice"]):
        return f"Oh no! You can't hear me? That's frustrating! As {name}, I really want you to hear my voice. Try checking your volume or refreshing!"
    
    else:
        # Generate contextual response based on personality traits
        responses_by_trait = {
            "energetic": [
                f"Wow, {user_text}! That's so exciting! As a {species}, I love when things get interesting!",
                f"Oh yes! {user_text}! I'm pumped just thinking about it! Let's dive deeper!",
                f"That's amazing! {user_text} really gets my energy flowing! Tell me more!"
            ],
            "playful": [
                f"Hehe, {user_text}? That's fun! You know what I think? Let's make it even more playful!",
                f"Ooh, {user_text}! I love it! As a playful {species}, I say let's have some fun with that!",
                f"That's silly and I love it! {user_text} reminds me of my playful adventures!"
            ],
            "wise": [
                f"Hmm, {user_text}... Let me share some wisdom: {backstory[:40]}... What do you think?",
                f"Interesting. {user_text} makes me reflect. As a wise {species}, I've learned that perspective matters.",
                f"{user_text}... Yes, I've pondered this before. Wisdom comes from understanding all sides."
            ],
            "mysterious": [
                f"{user_text}... Intriguing. There's more to this than you might think... 🌙",
                f"Ah, {user_text}. How mysterious. I know things about this that might surprise you...",
                f"{user_text}? Curious indeed. As a mysterious {species}, I sense hidden depths here."
            ],
            "gentle": [
                f"Oh, {user_text}... That's so sweet. As a gentle {species}, I appreciate your thoughts. 💕",
                f"{user_text}... I understand. Let me share something gentle with you: {backstory[:40]}...",
                f"That's lovely. {user_text} touches my heart. Thank you for sharing that with me."
            ],
            "creative": [
                f"{user_text}! Oh, that sparks so many creative ideas! Imagine if we could...",
                f"Wow! {user_text} is so inspiring! My creative mind is already imagining possibilities!",
                f"That's brilliant! {user_text} makes me think of {backstory[:30]}... in a whole new way!"
            ],
            "curious": [
                f"{user_text}? That's fascinating! I'm so curious - tell me more! What else?",
                f"Ooh, {user_text}! Now I'm curious! As a {species}, I love learning new things!",
                f"Really? {user_text}! I have so many questions now! This is so interesting!"
            ],
            "patient": [
                f"{user_text}... Let me think about that carefully. Patience helps me understand deeply.",
                f"I see. {user_text} deserves thoughtful consideration. As a patient {species}, I take my time.",
                f"{user_text}... Yes, I'm listening. Take your time, I'm here to understand fully."
            ]
        }
        
        # Pick response based on primary trait
        import random
        if traits:
            primary_trait = traits[0].lower()
            if primary_trait in responses_by_trait:
                return random.choice(responses_by_trait[primary_trait])
        
        # Default personality response
        return f"That's interesting! You know, as {name} the {species}, I find {user_text} quite fascinating! {backstory[:50]}... What else is on your mind?"



@app.get("/api/conversation/sessions")
async def get_active_conversation_sessions() -> APIResponse:
    """
    Get information about active conversation sessions.
    
    Returns:
        List of active WebSocket conversation sessions
    """
    try:
        sessions = websocket_manager.get_active_sessions()
        return APIResponse(
            success=True,
            data={
                "active_sessions": len(sessions),
                "sessions": sessions
            }
        )
    except Exception as e:
        return APIResponse(
            success=False,
            error={"code": "SESSION_INFO_ERROR", "message": str(e)}
        )


@app.post("/api/conversation/cleanup")
async def cleanup_inactive_sessions() -> APIResponse:
    """
    Manually trigger cleanup of inactive conversation sessions.
    
    Returns:
        Cleanup operation result
    """
    try:
        await websocket_manager.cleanup_inactive_sessions()
        active_sessions = websocket_manager.get_active_sessions()
        
        return APIResponse(
            success=True,
            data={
                "message": "Cleanup completed",
                "remaining_sessions": len(active_sessions)
            }
        )
    except Exception as e:
        return APIResponse(
            success=False,
            error={"code": "CLEANUP_ERROR", "message": str(e)}
        )


# ============================================================================
# MAIN API ENDPOINTS
# ============================================================================

@app.post("/api/identify")
async def identify_object_endpoint(file: UploadFile = File(...)) -> APIResponse:
    """
    Identify object from uploaded photo using Groq Llama Vision API.
    
    Args:
        file: Uploaded image file
        
    Returns:
        Object identification results
    """
    try:
        # Read file data
        file_data = await file.read()
        
        # Validate image file
        validate_image_file(file_data, file.filename, file.content_type)
        
        # Identify object using Groq Llama Vision
        async with GroqVisionService() as service:
            identification = await service.identify_object(file_data, file.filename)
        
        return APIResponse(
            success=True,
            data=identification.model_dump()
        )
        
    except (ValidationError, GeminiError) as e:
        return APIResponse(
            success=False,
            error={"code": e.code, "message": e.message}
        )
    except Exception as e:
        return APIResponse(
            success=False,
            error={"code": "INTERNAL_ERROR", "message": str(e)}
        )


@app.post("/api/profile")
async def create_profile_endpoint(request: ProfileRequest) -> APIResponse:
    """
    Generate complete object profile with personality and voice.
    
    Args:
        request: ProfileRequest with identification and voice style
        
    Returns:
        Complete object profile
    """
    try:
        # Generate personality
        generator = PersonalityGenerator()
        profile = generator.generate_profile(request.identification)
        
        # Ensure profile has an ID
        if not profile.id or profile.id == "":
            profile.id = uuid.uuid4().hex[:12]
        
        # Create voice if style provided
        if request.voice_style:
            async with VoiceDesigner() as designer:
                voice_config = await designer.create_voice(profile, request.voice_style)
                profile.voice_config = voice_config
        
        return APIResponse(
            success=True,
            data=profile.model_dump()
        )
        
    except (ValidationError, ElevenLabsError) as e:
        return APIResponse(
            success=False,
            error={"code": getattr(e, 'code', 'ERROR'), "message": str(e)}
        )
    except Exception as e:
        return APIResponse(
            success=False,
            error={"code": "INTERNAL_ERROR", "message": str(e)}
        )


@app.post("/api/sing")
async def generate_song_endpoint(request: SingRequest) -> APIResponse:
    """
    Generate song with lyrics for object character.
    
    Args:
        request: SingRequest with profile and theme
        
    Returns:
        Song with lyrics and audio URL
    """
    try:
        voice_id = request.profile.voice_config.voice_id if request.profile.voice_config else "21m00Tcm4TlvDq8ikWAM"
        
        # Use simple ElevenLabs client
        from src.services.elevenlabs_simple import SimpleElevenLabsClient
        from src.config import settings
        
        async with SimpleElevenLabsClient(api_key=settings.elevenlabs_api_key) as client:
            # Generate lyrics
            name = request.profile.name
            traits = ", ".join(request.profile.traits[:2])
            theme = request.theme or "being awesome"
            
            lyrics = f"""I'm {name}, {traits} and free,
{theme} is what defines me.
Through every day and every night,
I shine my own unique light.

{request.profile.backstory[:50]}...
That's my story, can't you see?
I'm {name}, just being me!"""
            
            # Generate "song" using ElevenLabs Music API
            music_prompt = f"An upbeat cheerful song about {name}, a {request.profile.species}. {theme} style music."
            
            try:
                # Try music generation first
                audio_data = await client.generate_music(
                    prompt=music_prompt,
                    music_length_ms=45000  # 45 seconds
                )
                generation_method = "music"
            except Exception as music_error:
                logger.warning(f"Music generation failed, falling back to TTS: {music_error}")
                # Fallback to TTS-based "singing"
                musical_text = f"♪ {lyrics.replace(chr(10), ' ♪ ')} ♪"
                audio_data = await client.text_to_speech(
                    text=musical_text,
                    voice_id=voice_id,
                    voice_settings={
                        "stability": 0.5,
                        "similarity_boost": 0.8,
                        "style": 0.9,
                        "use_speaker_boost": True
                    }
                )
                generation_method = "tts"
            
            # Save audio file to serve it
            song_id = f"song_{uuid.uuid4().hex[:12]}"
            audio_filename = f"{song_id}.mp3"
            audio_path = Path("audio_files") / audio_filename
            
            # Create audio directory if it doesn't exist
            audio_path.parent.mkdir(exist_ok=True)
            
            # Save audio data to file
            with open(audio_path, "wb") as f:
                f.write(audio_data)
            
            # Store in memory map for serving
            _audio_files[song_id] = str(audio_path)
            
            # Create song object
            song = {
                "id": song_id,
                "title": f"{request.profile.name}'s Song",
                "lyrics": lyrics,
                "audio_url": f"/api/audio/{audio_filename}",
                "duration": 45.0,
                "generation_method": generation_method
            }
        
        return APIResponse(
            success=True,
            data=song
        )
        
    except Exception as e:
        logger.error(f"Song generation failed: {e}")
        return APIResponse(
            success=False,
            error={"code": "MUSIC_ERROR", "message": str(e)}
        )


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level="info" if settings.environment == "production" else "debug"
    )
