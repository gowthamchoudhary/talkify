"""
Test ElevenLabs TTS endpoint specifically.
"""
import asyncio
import os
from dotenv import load_dotenv
import aiohttp

# Load environment variables
load_dotenv()

async def test_tts():
    """Test ElevenLabs TTS endpoint."""
    api_key = os.getenv("ELEVENLABS_API_KEY")
    
    if not api_key:
        print("❌ ELEVENLABS_API_KEY not found in environment")
        return False
    
    print(f"✓ API Key found: {api_key[:15]}...")
    
    # Test with Rachel voice (Mysterious)
    voice_id = "21m00Tcm4TlvDq8ikWAM"
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }
    
    payload = {
        "text": "Hello! This is a test of the ElevenLabs text to speech API.",
        "model_id": "eleven_turbo_v2_5",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.0,
            "use_speaker_boost": True
        }
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            print("\n🔄 Testing ElevenLabs TTS endpoint...")
            print(f"   Voice ID: {voice_id} (Rachel)")
            print(f"   Text: {payload['text']}")
            
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    audio_data = await response.read()
                    print(f"\n✅ TTS API is WORKING!")
                    print(f"   - Status: {response.status}")
                    print(f"   - Audio size: {len(audio_data)} bytes")
                    print(f"   - Content type: {response.headers.get('content-type')}")
                    
                    # Save audio file for verification
                    with open("test_output.mp3", "wb") as f:
                        f.write(audio_data)
                    print(f"   - Saved to: test_output.mp3")
                    
                    return True
                elif response.status == 401:
                    error_text = await response.text()
                    print(f"\n❌ API Key is INVALID for TTS (401 Unauthorized)")
                    print(f"   Response: {error_text}")
                    return False
                elif response.status == 403:
                    error_text = await response.text()
                    print(f"\n❌ API Key lacks TTS permission (403 Forbidden)")
                    print(f"   Response: {error_text}")
                    return False
                else:
                    error_text = await response.text()
                    print(f"\n⚠️  Unexpected response: {response.status}")
                    print(f"   Response: {error_text}")
                    return False
    except Exception as e:
        print(f"\n❌ Error testing TTS: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_all_voices():
    """Test all 6 pre-made voices."""
    api_key = os.getenv("ELEVENLABS_API_KEY")
    
    voices = {
        "Rachel (Mysterious)": "21m00Tcm4TlvDq8ikWAM",
        "Bella (Warm)": "EXAVITQu4vr4xnSDxMaL",
        "Antoni (Wise)": "ErXwobaYiN019PkySvjV",
        "Elli (Playful)": "MF3mGyEYCl7XYWbV9V6O",
        "Josh (Dramatic)": "TxGEqnHWrfWFTfGW9XjX",
        "Adam (Whispery)": "pNInz6obpgDQGcFmaJgB",
    }
    
    print("\n🎤 Testing all 6 pre-made voices:")
    print("-" * 60)
    
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }
    
    payload = {
        "text": "Testing voice.",
        "model_id": "eleven_turbo_v2_5",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }
    
    results = []
    
    async with aiohttp.ClientSession() as session:
        for name, voice_id in voices.items():
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            try:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        audio_data = await response.read()
                        print(f"   ✓ {name}: Working ({len(audio_data)} bytes)")
                        results.append(True)
                    else:
                        error = await response.text()
                        print(f"   ✗ {name}: Failed ({response.status})")
                        results.append(False)
            except Exception as e:
                print(f"   ✗ {name}: Error - {e}")
                results.append(False)
    
    return all(results)

async def main():
    """Run all tests."""
    print("=" * 60)
    print("🧪 ElevenLabs TTS Test Suite")
    print("=" * 60)
    
    # Test 1: Single TTS call
    tts_test = await test_tts()
    
    # Test 2: All voices
    if tts_test:
        print("\n")
        all_voices_test = await test_all_voices()
        
        print("\n" + "=" * 60)
        if all_voices_test:
            print("✅ All 6 voices are working!")
        else:
            print("⚠️  Some voices failed")
    else:
        print("\n" + "=" * 60)
        print("❌ TTS test failed - cannot proceed with voice tests")
    
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
