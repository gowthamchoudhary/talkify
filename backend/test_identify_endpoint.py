"""
Test the /api/identify endpoint directly
"""
import asyncio
import aiohttp
import sys
from pathlib import Path

async def test_identify_endpoint():
    """Test the identify endpoint with a simple file."""
    
    print("=" * 60)
    print("Testing /api/identify Endpoint")
    print("=" * 60)
    
    # Read the test image file
    with open('test_coffee.jpg', 'rb') as f:
        test_content = f.read()
    
    # Create form data
    data = aiohttp.FormData()
    data.add_field('file', test_content, filename='coffee.jpg', content_type='image/jpeg')
    
    url = "http://localhost:8000/api/identify"
    
    print("🔄 Testing identify endpoint...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data) as response:
                if response.status != 200:
                    error = await response.text()
                    print(f"❌ ERROR: {error}")
                    return False
                
                result = await response.json()
                
                print("\n✅ SUCCESS! Identify endpoint is working!")
                print("-" * 60)
                print("Full response:", result)
                print("-" * 60)
                
                return True
                
    except Exception as e:
        print(f"❌ ERROR: {e}")
        print("\nMake sure the backend is running on http://localhost:8000")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_identify_endpoint())
    sys.exit(0 if success else 1)