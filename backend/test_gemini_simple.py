"""
Simple Gemini API test without images
"""
import asyncio
import aiohttp
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from src.config import settings


async def test_gemini_text():
    """Test Gemini API with text-only request."""
    
    print("=" * 60)
    print("Testing Gemini API (Text Only)")
    print("=" * 60)
    
    api_key = settings.gemini_api_key
    if not api_key:
        print("❌ ERROR: GEMINI_API_KEY not configured")
        return False
    
    print(f"✅ API Key: {api_key[:20]}...")
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{
                "text": "Describe a coffee mug as if it were alive with a personality. Give it a name, 3 personality traits, and a short backstory. Format as JSON with keys: name, traits (array), backstory."
            }]
        }]
    }
    
    print("\n🔄 Calling Gemini API...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    error = await response.text()
                    print(f"❌ ERROR: {error}")
                    return False
                
                result = await response.json()
                
                # Extract text
                text = result["candidates"][0]["content"]["parts"][0]["text"]
                
                print("\n✅ SUCCESS! Gemini API is working!")
                print("-" * 60)
                print(text)
                print("-" * 60)
                
                return True
                
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_gemini_text())
    sys.exit(0 if success else 1)
