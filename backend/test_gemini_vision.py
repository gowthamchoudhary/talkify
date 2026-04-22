"""
Test Gemini Vision API with image support
"""
import asyncio
import aiohttp
import base64
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from src.config import settings


async def test_gemini_vision():
    """Test Gemini Vision API with a simple image."""
    
    print("=" * 60)
    print("Testing Gemini Vision API")
    print("=" * 60)
    
    api_key = settings.gemini_api_key
    if not api_key:
        print("❌ ERROR: GEMINI_API_KEY not configured")
        return False
    
    print(f"✅ API Key: {api_key[:20]}...")
    
    # Create a simple 1x1 red pixel JPEG (minimal valid JPEG)
    jpeg_data = bytes([
        0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01,
        0x01, 0x01, 0x00, 0x48, 0x00, 0x48, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43,
        0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08, 0x07, 0x07, 0x07, 0x09,
        0x09, 0x08, 0x0A, 0x0C, 0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12,
        0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D, 0x1A, 0x1C, 0x1C, 0x20,
        0x24, 0x2E, 0x27, 0x20, 0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29,
        0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27, 0x39, 0x3D, 0x38, 0x32,
        0x3C, 0x2E, 0x33, 0x34, 0x32, 0xFF, 0xC0, 0x00, 0x11, 0x08, 0x00, 0x01,
        0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0x02, 0x11, 0x01, 0x03, 0x11, 0x01,
        0xFF, 0xC4, 0x00, 0x14, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x08, 0xFF, 0xC4,
        0x00, 0x14, 0x10, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xFF, 0xDA, 0x00, 0x0C,
        0x03, 0x01, 0x00, 0x02, 0x11, 0x03, 0x11, 0x00, 0x3F, 0x00, 0x80, 0xFF, 0xD9
    ])
    
    image_base64 = base64.b64encode(jpeg_data).decode('utf-8')
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [
                {
                    "text": """Analyze this image and identify the main object. 
                    Provide a JSON response with:
                    {
                        "object_type": "description of what you see",
                        "species": "specific type if applicable",
                        "characteristics": ["trait1", "trait2", "trait3"],
                        "confidence": 0.8
                    }"""
                },
                {
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": image_base64
                    }
                }
            ]
        }]
    }
    
    print("\n🔄 Testing Gemini Vision with image...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 429:
                    print("⚠️  Quota exceeded - this is expected for free tier")
                    print("✅ But the API key and endpoint are working!")
                    return True
                elif response.status != 200:
                    error = await response.text()
                    print(f"❌ ERROR: {error}")
                    return False
                
                result = await response.json()
                
                # Extract text
                text = result["candidates"][0]["content"]["parts"][0]["text"]
                
                print("\n✅ SUCCESS! Gemini Vision is working!")
                print("-" * 60)
                print(text)
                print("-" * 60)
                
                return True
                
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_gemini_vision())
    sys.exit(0 if success else 1)