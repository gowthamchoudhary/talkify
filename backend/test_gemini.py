"""
Quick test script for Gemini Vision API
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.services.gemini_vision import GeminiVisionService
from src.config import settings


async def test_gemini():
    """Test Gemini Vision with a simple prompt."""
    
    print("=" * 60)
    print("Testing Gemini Vision API")
    print("=" * 60)
    
    # Check API key
    if not settings.gemini_api_key:
        print("❌ ERROR: GEMINI_API_KEY not configured in .env")
        return False
    
    print(f"✅ API Key configured: {settings.gemini_api_key[:20]}...")
    
    # Create a simple test image (1x1 red pixel PNG)
    # This is a valid minimal PNG file
    test_image = bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1 dimensions
        0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
        0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,  # IDAT chunk
        0x54, 0x08, 0xD7, 0x63, 0xF8, 0xCF, 0xC0, 0x00,
        0x00, 0x03, 0x01, 0x01, 0x00, 0x18, 0xDD, 0x8D,
        0xB4, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,  # IEND chunk
        0x44, 0xAE, 0x42, 0x60, 0x82
    ])
    
    print("\n📸 Testing with a simple test image...")
    
    try:
        async with GeminiVisionService() as service:
            print("🔄 Calling Gemini Vision API...")
            
            result = await service.identify_object(
                image_data=test_image,
                filename="test.png"
            )
            
            print("\n✅ SUCCESS! Gemini Vision is working!")
            print("-" * 60)
            print(f"Object Type: {result.object_type}")
            print(f"Species: {result.species}")
            print(f"Characteristics: {', '.join(result.characteristics)}")
            print(f"Confidence: {result.confidence:.2%}")
            print("-" * 60)
            
            return True
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nPossible issues:")
        print("1. Invalid API key")
        print("2. API quota exceeded")
        print("3. Network connectivity issue")
        print("4. API endpoint changed")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_gemini())
    sys.exit(0 if success else 1)
