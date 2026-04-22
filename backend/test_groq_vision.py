"""
Test Groq Llama Vision API
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.services.groq_vision import GroqVisionService
from src.config import settings


async def test_groq_vision():
    """Test Groq Llama Vision API with a real image."""
    
    print("=" * 60)
    print("Testing Groq Llama Vision API")
    print("=" * 60)
    
    # Check API key
    if not settings.groq_api_key:
        print("❌ ERROR: GROQ_API_KEY not configured in .env")
        return False
    
    print(f"✅ API Key configured: {settings.groq_api_key[:20]}...")
    
    # Read the test image
    try:
        with open('test_coffee.jpg', 'rb') as f:
            image_data = f.read()
    except FileNotFoundError:
        print("❌ ERROR: test_coffee.jpg not found. Run create_test_image.py first")
        return False
    
    print(f"\n📸 Testing with test_coffee.jpg ({len(image_data)} bytes)...")
    
    try:
        async with GroqVisionService() as service:
            print("🔄 Calling Groq Llama Vision API...")
            
            result = await service.identify_object(
                image_data=image_data,
                filename="test_coffee.jpg"
            )
            
            print("\n✅ SUCCESS! Groq Llama Vision is working!")
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
        print("2. Rate limit exceeded")
        print("3. Network connectivity issue")
        print("4. Model not available")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_groq_vision())
    sys.exit(0 if success else 1)