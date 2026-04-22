"""
Talkify FastAPI Application
Main application entry point with middleware, dependencies, and core endpoints.
"""
import os
import time
import uuid
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

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
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
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
    Convert text to speech using ElevenLabs TTS v3 API with emotional tags.
    
    Args:
        request: SpeakRequest containing text and voice configuration
        
    Returns:
        Audio URL and metadata for playback
    """
    try:
        async with ElevenLabsService() as service:
            # Get session ID from voice config or generate one
            session_id = f"tts_session_{int(time.time())}"
            
            # Get conversation context for emotional analysis
            conversation_context = service.get_conversation_context(session_id)
            
            # Convert text to speech using TTS v3 with emotional tags
            audio_data = await service.text_to_speech_v3(
                text=request.text,
                voice_id=request.voice_config.voice_id,
                voice_settings=request.voice_config.settings,
                conversation_context=conversation_context,
                audio_format="mp3",
                enable_streaming=True
            )
            
            # Add the text to conversation context for future emotional analysis
            service.add_conversation_message(session_id, request.text)
            
            # In a production environment, you would save the audio to a file storage service
            # and return the URL. For now, we'll return a placeholder URL with metadata
            audio_url = f"/api/audio/{session_id}_{int(time.time())}.mp3"
            
            # Detect emotional tags for response metadata
            emotional_tags = service._detect_emotional_tags(request.text, conversation_context)
            
            return APIResponse(
                success=True,
                data={
                    "audio_url": audio_url,
                    "session_id": session_id,
                    "text": request.text,
                    "voice_id": request.voice_config.voice_id,
                    "emotional_tags": emotional_tags,
                    "audio_format": "mp3",
                    "audio_size_bytes": len(audio_data),
                    "duration_estimate": len(request.text) * 0.1,  # Rough estimate: 0.1s per character
                    "voice_style": request.voice_config.style.value
                }
            )
        
    except ElevenLabsError as e:
        return APIResponse(
            success=False,
            error={"code": "TTS_ERROR", "message": str(e)}
        )
    except Exception as e:
        return APIResponse(
            success=False,
            error={"code": "INTERNAL_ERROR", "message": str(e)}
        )


@app.post("/api/ambient")
async def generate_ambient_sounds(request: AmbientRequest) -> APIResponse:
    """
    Generate ambient sound effects using ElevenLabs Sound Effects API.
    
    Args:
        request: AmbientRequest containing object type and intensity
        
    Returns:
        Ambient audio URL and metadata for background playback
        
    Requirements: 6.1, 6.2, 6.4, 11.4
    """
    try:
        async with ElevenLabsService() as service:
            # Generate contextual ambient sounds based on object type
            ambient_audio = await service.generate_sound_effects(
                object_type=request.object_type,
                intensity=request.intensity,
                duration_seconds=60,  # Default 60 seconds for ambient loops
                audio_format="mp3"
            )
            
            # Generate session ID for ambient audio tracking
            ambient_session_id = f"ambient_{request.object_type}_{int(time.time())}"
            
            # In production, save audio to file storage and return URL
            ambient_url = f"/api/audio/ambient/{ambient_session_id}.mp3"
            
            # Get sound description for metadata
            sound_info = service._get_sound_description_for_object(request.object_type)
            
            return APIResponse(
                success=True,
                data={
                    "ambient_url": ambient_url,
                    "session_id": ambient_session_id,
                    "object_type": request.object_type,
                    "intensity": request.intensity,
                    "duration_seconds": 60,
                    "audio_format": "mp3",
                    "audio_size_bytes": len(ambient_audio),
                    "sound_description": sound_info["primary_description"],
                    "mood": sound_info["mood"],
                    "secondary_sounds": sound_info.get("secondary_sounds", []),
                    "volume_mixed": True,  # Indicates audio is pre-mixed for speech compatibility
                    "conversation_ready": True  # Indicates audio is optimized for conversation use
                }
            )
        
    except ElevenLabsError as e:
        return APIResponse(
            success=False,
            error={"code": "AMBIENT_GENERATION_ERROR", "message": str(e)}
        )
    except Exception as e:
        return APIResponse(
            success=False,
            error={"code": "INTERNAL_ERROR", "message": str(e)}
        )


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


@app.websocket("/ws/conversation")
async def websocket_conversation_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time voice conversation.
    
    Handles real-time audio input/output for conversations with AI characters.
    Maintains conversation context and session state throughout the interaction.
    
    Requirements: 5.1, 5.4, 5.8, 10.6, 11.3
    """
    session_id = None
    try:
        # Generate unique session ID
        session_id = f"ws_session_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        # Connect WebSocket
        connected = await websocket_manager.connect(websocket, session_id)
        if not connected:
            await websocket.close(code=1011, reason="Failed to establish connection")
            return
        
        # Main message loop
        while True:
            try:
                # Check if we're receiving text (JSON) or binary (audio) data
                message = await websocket.receive()
                
                if "text" in message:
                    # Handle JSON message
                    import json
                    try:
                        data = json.loads(message["text"])
                        await websocket_manager.handle_message(session_id, data)
                    except json.JSONDecodeError as e:
                        await websocket_manager.send_message(session_id, {
                            "type": "error",
                            "error": "invalid_json",
                            "message": f"Invalid JSON format: {e}"
                        })
                
                elif "bytes" in message:
                    # Handle binary audio data
                    audio_data = message["bytes"]
                    await websocket_manager.handle_audio_data(session_id, audio_data)
                
                else:
                    await websocket_manager.send_message(session_id, {
                        "type": "error",
                        "error": "invalid_message_format",
                        "message": "Message must contain either text or bytes"
                    })
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                await websocket_manager.send_message(session_id, {
                    "type": "error",
                    "error": "message_processing_error",
                    "message": str(e)
                })
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        if session_id:
            try:
                await websocket_manager.send_message(session_id, {
                    "type": "error",
                    "error": "connection_error",
                    "message": str(e)
                })
            except:
                pass
    finally:
        if session_id:
            await websocket_manager.disconnect(session_id)


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


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level="info" if settings.environment == "production" else "debug"
    )
