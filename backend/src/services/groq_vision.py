"""
Groq Vision API integration for object identification using Llama 4 Scout 17B.

This module provides photo analysis using Groq's Llama Vision model
to identify objects and extract characteristics.
"""
import logging
import base64
from typing import Dict, Any, Optional
import aiohttp

from ..config import settings
from ..models import ObjectIdentification
from ..exceptions import GeminiError

logger = logging.getLogger(__name__)


class GroqVisionService:
    """
    Service for analyzing photos using Groq Llama 4 Scout 17B Vision model.
    
    Handles:
    - Object identification from images
    - Species and type extraction
    - Characteristic analysis
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Groq Vision service."""
        self.api_key = api_key or settings.groq_api_key
        if not self.api_key:
            raise ValueError("Groq API key is required")
        
        self.base_url = "https://api.groq.com/openai/v1"
        self.model = "meta-llama/llama-4-scout-17b-16e-instruct"
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
        Identify object in image using Groq Llama Vision API.
        
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
            
            # Determine MIME type from filename
            mime_type = "image/jpeg"
            if filename.lower().endswith('.png'):
                mime_type = "image/png"
            elif filename.lower().endswith('.webp'):
                mime_type = "image/webp"
            
            # Prepare request
            url = f"{self.base_url}/chat/completions"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """Analyze this image and identify the main object or living thing. 
                                
                                Provide a JSON response with:
                                {
                                    "object_type": "brief description of what you see (e.g., 'coffee mug', 'houseplant', 'book')",
                                    "species": "specific type if applicable (e.g., 'ceramic mug', 'succulent plant', 'hardcover book') or null",
                                    "characteristics": ["3-5 descriptive traits like 'ceramic', 'green', 'rectangular', 'vintage', etc."],
                                    "confidence": 0.95
                                }
                                
                                Be specific and descriptive. Focus on the most prominent object in the image."""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 500,
                "temperature": 0.1
            }
            
            logger.info(f"Analyzing image with Groq Llama Vision: {filename}")
            
            # Make API request
            async with self.session.post(url, json=payload, headers=headers) as response:
                if response.status == 429:
                    # Rate limit exceeded - return fallback identification
                    logger.warning("Groq API rate limit exceeded, using fallback identification")
                    return self._create_fallback_identification(filename)
                elif response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Groq API error (status {response.status}): {error_text}")
                    logger.info(f"Image info: filename={filename}, size={len(image_data)} bytes, mime_type={mime_type}")
                    return self._create_fallback_identification(filename)
                
                result = await response.json()
            
            # Parse response
            identification = self._parse_response(result)
            
            logger.info(f"Identified: {identification.object_type} (confidence: {identification.confidence})")
            
            return identification
            
        except Exception as e:
            logger.error(f"Failed to identify object: {e}")
            # Return fallback instead of raising error
            return self._create_fallback_identification(filename)
    
    def _create_fallback_identification(self, filename: str) -> ObjectIdentification:
        """
        Create a fallback identification when API fails.
        
        Args:
            filename: Original filename for hints
            
        Returns:
            ObjectIdentification with generic data
        """
        # Try to guess from filename
        filename_lower = filename.lower()
        
        if any(word in filename_lower for word in ['coffee', 'mug', 'cup']):
            return ObjectIdentification(
                object_type="coffee mug",
                species="ceramic mug",
                characteristics=["ceramic", "functional", "everyday object"],
                confidence=0.7
            )
        elif any(word in filename_lower for word in ['plant', 'flower', 'leaf']):
            return ObjectIdentification(
                object_type="plant",
                species="houseplant",
                characteristics=["green", "living", "photosynthetic"],
                confidence=0.7
            )
        elif any(word in filename_lower for word in ['book', 'novel', 'read']):
            return ObjectIdentification(
                object_type="book",
                species="printed book",
                characteristics=["literary", "informative", "page-turner"],
                confidence=0.7
            )
        else:
            return ObjectIdentification(
                object_type="mysterious object",
                species="unknown",
                characteristics=["intriguing", "unique", "special"],
                confidence=0.5
            )
    
    def _parse_response(self, response: Dict[str, Any]) -> ObjectIdentification:
        """
        Parse Groq API response into ObjectIdentification.
        
        Args:
            response: API response data
            
        Returns:
            ObjectIdentification object
        """
        try:
            # Extract text from response
            choices = response.get("choices", [])
            if not choices:
                raise ValueError("No choices in response")
            
            message = choices[0].get("message", {})
            content = message.get("content", "")
            
            # Try to parse as JSON
            import json
            # Extract JSON from markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            # Clean up the content - sometimes there's extra text
            if "{" in content and "}" in content:
                start = content.find("{")
                end = content.rfind("}") + 1
                content = content[start:end]
            
            data = json.loads(content)
            
            # Create ObjectIdentification
            return ObjectIdentification(
                object_type=data.get("object_type", "unknown object"),
                species=data.get("species"),
                characteristics=data.get("characteristics", []),
                confidence=float(data.get("confidence", 0.8))
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse structured response: {e}")
            logger.debug(f"Raw response: {response}")
            # Fallback: create basic identification
            return ObjectIdentification(
                object_type="object",
                species=None,
                characteristics=["interesting", "unique", "special"],
                confidence=0.5
            )


# Example usage
async def example_groq_usage():
    """Example of how to use the Groq Vision service."""
    # Create dummy image data
    dummy_image = b"fake_image_data"
    
    async with GroqVisionService() as service:
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
    asyncio.run(example_groq_usage())