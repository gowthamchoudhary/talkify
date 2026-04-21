"""
Google Gemini Vision API integration for object identification.

This module provides photo analysis using Google Gemini Vision API
to identify objects and extract characteristics.

Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
"""
import logging
import base64
from typing import Dict, Any, Optional
import aiohttp

from ..config import settings
from ..models import ObjectIdentification
from ..exceptions import GeminiError

logger = logging.getLogger(__name__)


class GeminiVisionService:
    """
    Service for analyzing photos using Google Gemini Vision API.
    
    Handles:
    - Object identification from images
    - Species and type extraction
    - Characteristic analysis
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Gemini Vision service."""
        self.api_key = api_key or settings.gemini_api_key
        if not self.api_key:
            raise ValueError("Gemini API key is required")
        
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.model = "gemini-1.5-flash"
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def identify_object(
        self,
        image_data: bytes,
        filename: str = "image.jpg"
    ) -> ObjectIdentification:
        """
        Identify object in image using Gemini Vision API.
        
        Args:
            image_data: Image bytes
            filename: Original filename
            
        Returns:
            ObjectIdentification with type, species, and characteristics
            
        Raises:
            GeminiError: If identification fails
        """
        try:
            # Encode image to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Prepare request
            url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
            
            payload = {
                "contents": [{
                    "parts": [
                        {
                            "text": """Analyze this image and identify the main object or living thing. 
                            Provide:
                            1. Object type (e.g., "cat", "book", "flower")
                            2. Species if applicable (e.g., "domestic cat", "rose")
                            3. 3-5 descriptive characteristics (e.g., "fluffy", "orange", "playful")
                            
                            Format your response as JSON:
                            {
                                "object_type": "...",
                                "species": "..." or null,
                                "characteristics": ["...", "...", "..."],
                                "confidence": 0.0-1.0
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
            
            logger.info(f"Analyzing image: {filename}")
            
            # Make API request
            async with self.session.post(url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise GeminiError(f"API error: {error_text}", response.status)
                
                result = await response.json()
            
            # Parse response
            identification = self._parse_response(result)
            
            logger.info(f"Identified: {identification.object_type} (confidence: {identification.confidence})")
            
            return identification
            
        except GeminiError:
            raise
        except Exception as e:
            logger.error(f"Failed to identify object: {e}")
            raise GeminiError(f"Object identification failed: {str(e)}")
    
    def _parse_response(self, response: Dict[str, Any]) -> ObjectIdentification:
        """
        Parse Gemini API response into ObjectIdentification.
        
        Args:
            response: API response data
            
        Returns:
            ObjectIdentification object
        """
        try:
            # Extract text from response
            candidates = response.get("candidates", [])
            if not candidates:
                raise ValueError("No candidates in response")
            
            content = candidates[0].get("content", {})
            parts = content.get("parts", [])
            if not parts:
                raise ValueError("No parts in response")
            
            text = parts[0].get("text", "")
            
            # Try to parse as JSON
            import json
            # Extract JSON from markdown code blocks if present
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            data = json.loads(text)
            
            # Create ObjectIdentification
            return ObjectIdentification(
                object_type=data.get("object_type", "unknown object"),
                species=data.get("species"),
                characteristics=data.get("characteristics", []),
                confidence=float(data.get("confidence", 0.8))
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse structured response: {e}")
            # Fallback: create basic identification
            return ObjectIdentification(
                object_type="object",
                species=None,
                characteristics=["interesting", "unique", "special"],
                confidence=0.5
            )


# Example usage
async def example_gemini_usage():
    """Example of how to use the Gemini Vision service."""
    # Create dummy image data
    dummy_image = b"fake_image_data"
    
    async with GeminiVisionService() as service:
        identification = await service.identify_object(
            image_data=dummy_image,
            filename="test.jpg"
        )
        
        print(f"Object: {identification.object_type}")
        print(f"Species: {identification.species}")
        print(f"Characteristics: {identification.characteristics}")
        print(f"Confidence: {identification.confidence}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_gemini_usage())
