"""
Quick test script to verify ElevenLabs API key is working.
"""
import asyncio
import os
from dotenv import load_dotenv
import aiohttp

# Load environment variables
load_dotenv()

async def test_elevenlabs_api():
    """Test ElevenLabs API key by fetching user info."""
    api_key = os.getenv("ELEVENLABS_API_KEY")
    
    if not api_key:
        print("❌ ELEVENLABS_API_KEY not found in environment")
        return False
    
    print(f"✓ API Key found: {api_key[:15]}...")
    
    # Test API by getting user info
    url = "https://api.elevenlabs.io/v1/user"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            print("\n🔄 Testing ElevenLabs API connection...")
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ ElevenLabs API is WORKING!")
                    print(f"\n📊 Account Info:")
                    print(f"   - Subscription: {data.get('subscription', {}).get('tier', 'Unknown')}")
                    print(f"   - Character Count: {data.get('subscription', {}).get('character_count', 0)}")
                    print(f"   - Character Limit: {data.get('subscription', {}).get('character_limit', 0)}")
                    print(f"   - Can Use Instant Voice Cloning: {data.get('subscription', {}).get('can_use_instant_voice_cloning', False)}")
                    return True
                elif response.status == 401:
                    print(f"❌ API Key is INVALID (401 Unauthorized)")
                    print(f"   Response: {await response.text()}")
                    return False
                else:
                    print(f"⚠️  Unexpected response: {response.status}")
                    print(f"   Response: {await response.text()}")
                    return False
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        return False

async def test_voice_list():
    """Test fetching available voices."""
    api_key = os.getenv("ELEVENLABS_API_KEY")
    url = "https://api.elevenlabs.io/v1/voices"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            print("\n🔄 Testing voice list endpoint...")
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    voices = data.get('voices', [])
                    print(f"✅ Voice list endpoint working!")
                    print(f"   - Available voices: {len(voices)}")
                    
                    # Check if our pre-made voices are available
                    voice_ids = {
                        "Rachel (Mysterious)": "21m00Tcm4TlvDq8ikWAM",
                        "Bella (Warm)": "EXAVITQu4vr4xnSDxMaL",
                        "Antoni (Wise)": "ErXwobaYiN019PkySvjV",
                        "Elli (Playful)": "MF3mGyEYCl7XYWbV9V6O",
                        "Josh (Dramatic)": "TxGEqnHWrfWFTfGW9XjX",
                        "Adam (Whispery)": "pNInz6obpgDQGcFmaJgB",
                    }
                    
                    print(f"\n🎤 Checking pre-made voices:")
                    available_voice_ids = [v.get('voice_id') for v in voices]
                    for name, voice_id in voice_ids.items():
                        if voice_id in available_voice_ids:
                            print(f"   ✓ {name}: Available")
                        else:
                            print(f"   ✗ {name}: Not found")
                    
                    return True
                else:
                    print(f"⚠️  Voice list failed: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Error fetching voices: {e}")
        return False

async def main():
    """Run all tests."""
    print("=" * 60)
    print("🧪 ElevenLabs API Test Suite")
    print("=" * 60)
    
    # Test 1: User info
    user_test = await test_elevenlabs_api()
    
    # Test 2: Voice list
    if user_test:
        voice_test = await test_voice_list()
    
    print("\n" + "=" * 60)
    if user_test:
        print("✅ ElevenLabs API is configured correctly!")
    else:
        print("❌ ElevenLabs API test failed!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
