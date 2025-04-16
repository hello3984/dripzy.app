import base64
import logging
from io import BytesIO
from typing import Dict, List, Any, Optional
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

def create_brand_display(brand_data: Dict[str, List[str]]) -> Dict[str, str]:
    """
    Create a formatted brand display from the brand data.
    
    Args:
        brand_data: Dictionary with category as key and list of brands as value
                   Example: {"Tops": ["Nike", "Adidas"], "Bottoms": ["Levi's"]}
    
    Returns:
        Dictionary with formatted brand display strings
        Example: {"Tops": "Nike, Adidas", "Bottoms": "Levi's"}
    """
    try:
        brand_display = {}
        for category, brands in brand_data.items():
            # Ensure category is properly pluralized
            category_plural = category
            if not category.endswith('s'):
                category_plural = f"{category}s"
                
            # Join brands with commas
            brand_display[category_plural] = ", ".join(brands)
            
        logger.info(f"Created brand display: {brand_display}")
        return brand_display
    except Exception as e:
        logger.error(f"Error creating brand display: {str(e)}")
        return {}

def create_brand_image(brand_data: Dict[str, List[str]], width: int = 800, height: int = 200) -> Optional[str]:
    """
    Generate an image showing the brands used in an outfit.
    
    Args:
        brand_data: Dictionary with category as key and list of brands as value
        width: Width of the image to generate
        height: Height of the image to generate
        
    Returns:
        Base64 encoded image string or None if generation fails
    """
    try:
        # Create a blank image with white background
        image = Image.new('RGB', (width, height), color=(255, 255, 255))
        draw = ImageDraw.Draw(image)
        
        # Try to load a font, fall back to default if not available
        try:
            font_title = ImageFont.truetype("Arial.ttf", 24)
            font_brand = ImageFont.truetype("Arial.ttf", 18)
        except IOError:
            font_title = ImageFont.load_default()
            font_brand = ImageFont.load_default()
        
        # Draw title
        draw.text((20, 20), "Featured Brands", fill=(0, 0, 0), font=font_title)
        
        # Draw brand categories
        y_position = 60
        for category, brands in brand_data.items():
            # Format category name
            category_text = category if category.endswith('s') else f"{category}s"
            
            # Draw category name
            draw.text((40, y_position), f"{category_text}:", fill=(80, 80, 80), font=font_brand)
            
            # Draw brands
            draw.text((160, y_position), ", ".join(brands), fill=(0, 0, 0), font=font_brand)
            
            y_position += 30
        
        # Convert the image to base64
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return img_str
    except Exception as e:
        logger.error(f"Error creating brand image: {str(e)}")
        return None 