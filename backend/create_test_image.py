"""
Create a simple test image for testing
"""
from PIL import Image
import io

# Create a simple 100x100 red square
img = Image.new('RGB', (100, 100), color='red')

# Save as JPEG
img_bytes = io.BytesIO()
img.save(img_bytes, format='JPEG')
img_bytes.seek(0)

# Write to file
with open('test_coffee.jpg', 'wb') as f:
    f.write(img_bytes.getvalue())

print("✅ Created test_coffee.jpg")