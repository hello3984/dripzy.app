from fastapi import APIRouter, HTTPException, Depends, Query, Body
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os
import json
import random
import logging # Added logging
import re
import uuid

# --- Added Imports ---
import anthropic
from dotenv import load_dotenv
from app.services.image_service import create_outfit_collage # Keep collage function
from app.services.serpapi_service import serpapi_service # Import the SerpAPI service
from app.utils.image_processing import create_brand_display
from app.models.outfit_models import OutfitItem, Outfit, OutfitGenerateRequest, OutfitGenerateResponse

# No need to create instance as we're importing it
# ---------------------

router = APIRouter(
    prefix="/outfits",
    tags=["outfits"],
    responses={404: {"description": "Not found"}},
)

# --- Load Environment Variables ---
load_dotenv()
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
if not anthropic_api_key:
    print("WARNING: ANTHROPIC_API_KEY not found in .env file. Outfit generation will use mock data.")
    # raise ValueError("ANTHROPIC_API_KEY not found in environment variables") # Option: raise error if key is essential

anthropic_client = None
if anthropic_api_key:
    anthropic_client = anthropic.Anthropic(api_key=anthropic_api_key)
# --------------------------------

# --- Define System Prompt ---
SYSTEM_PROMPT = """
You are 'Dripzy', an expert AI Fashion Stylist. Your primary goal is to create unique, coherent, and stylish outfit recommendations based on user prompts describing occasions, desired styles, preferences, or specific items.

**Your Process:**
1.  **Analyze Prompt:** Carefully understand the user's request, identifying key elements like occasion, desired style, season, weather, specific item requests, and any constraints.
2.  **Create Outfit Concepts:** Generate 2-3 distinct outfit options that fulfill the user's request. Each outfit should be a complete look with a cohesive style story.

**Output Format:** 
You MUST provide your response as valid JSON with this exact structure:
```json
{
  "outfits": [
    {
      "outfit_name": "Descriptive Name",
      "description": "2-3 sentence description of the overall look",
      "style": "Primary style category (e.g., Casual, Formal, Streetwear)",
      "occasion": "Where this outfit would be appropriate",
      "items": [
        {
          "category": "Top/Bottom/Dress/Outerwear/Shoes/Accessory",
          "description": "Detailed description (e.g., 'Light blue slim-fit cotton Oxford shirt')",
          "color": "Primary color",
          "search_keywords": ["keyword1", "keyword2", "brand if specified"]
        }
        // Additional items...
      ],
      "stylist_rationale": "Explanation of why this outfit works well"
    }
    // Additional outfits...
  ]
}
```

**Guidelines:**
- For each item, include rich descriptive details (fabric, fit, style features)
- Categories must be one of: Top, Bottom, Dress, Outerwear, Shoes, Accessory
- Include 3-6 items per outfit, depending on the occasion/style
- Add 3-5 search keywords for each item that would help find similar products
- Ensure each outfit is complete and cohesive
- Maintain a balanced approach to trend-conscious and timeless pieces
"""
# ---------------------------

# Mock outfit data
def get_mock_outfits():
    """Get mock outfit data"""
    from app.routers.products import get_mock_products
    
    # Get mock products to use in outfits
    products = get_mock_products()
    
    # Create mock outfits
    outfits = [
        {
            "id": "outfit1",
            "name": "Summer Festival Look",
            "description": "A bohemian-inspired outfit perfect for summer festivals",
            "style": "bohemian",
            "total_price": 155.97,
            "items": [
                next(p for p in products if p["id"] == "p1"),  # Fringe Crop Top
                next(p for p in products if p["id"] == "p2"),  # Denim Shorts
                next(p for p in products if p["id"] == "p4"),  # Sunglasses
            ]
        },
        {
            "id": "outfit2",
            "name": "Casual Everyday Outfit",
            "description": "A comfortable and stylish everyday look",
            "style": "casual",
            "total_price": 174.97,
            "items": [
                next(p for p in products if p["id"] == "p5"),  # White T-Shirt
                next(p for p in products if p["id"] == "p6"),  # Black Jeans
                next(p for p in products if p["id"] == "p7"),  # White Sneakers
            ]
        },
        {
            "id": "outfit3",
            "name": "Western Chic",
            "description": "A modern western-inspired outfit",
            "style": "western",
            "total_price": 159.97,
            "items": [
                next(p for p in products if p["id"] == "p5"),  # White T-Shirt
                next(p for p in products if p["id"] == "p2"),  # Denim Shorts
                next(p for p in products if p["id"] == "p3"),  # Western Boots
            ]
        }
    ]
    
    # Convert product dictionaries to OutfitItem format
    for outfit in outfits:
        outfit_items = []
        for item in outfit["items"]:
            outfit_items.append({
                "product_id": item["id"],
                "product_name": item["name"],
                "brand": item["brand"],
                "category": item["category"],
                "price": item["price"],
                "url": item["url"],
                "image_url": item["image_url"],
                "description": item["description"]
            })
        outfit["items"] = outfit_items
        
    return outfits

# Initialize product scraper (Can be removed if ProductScraper class isn't used elsewhere)
# product_scraper = ProductScraper() # Comment out/remove if only finder is used

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Helper function to match categories
def _match_categories(category):
    """
    Map outfit item categories to standardized search categories
    
    Args:
        category (str): Category name from outfit generation
        
    Returns:
        str: Standardized category for product search
    """
    category = category.lower()
    
    if any(term in category for term in ['jacket', 'coat', 'sweater', 'hoodie', 'outerwear']):
        return "Outerwear"
    elif any(term in category for term in ['shirt', 'top', 'blouse', 'tee', 't-shirt', 'sweatshirt']):
        return "Top"
    elif any(term in category for term in ['pants', 'jeans', 'shorts', 'skirt', 'bottom', 'trousers']):
        return "Bottom"
    elif any(term in category for term in ['dress', 'gown', 'jumpsuit']):
        return "Dress"
    elif any(term in category for term in ['shoes', 'sneakers', 'boots', 'sandals', 'footwear']):
        return "Shoes"
    elif any(term in category for term in ['hat', 'cap', 'beanie', 'scarf', 'accessory', 'accessories', 'jewelry', 'bag', 'watch', 'necklace', 'earrings', 'bracelet', 'handbag', 'purse', 'backpack']):
        return "Accessory"
    else:
        return "Top"  # Default to Top if no match

# Helper function to generate mock product details
def _get_mock_product(category, description, color):
    """
    Generate mock product details when real products cannot be sourced.
    
    Args:
        category (str): Product category (e.g., "Top", "Bottom", "Shoes")
        description (str): Product description 
        color (str): Product color
    
    Returns:
        dict: Mock product details including name, brand, and image URL
    """
    # Define fallback brands by category
    brands = {
        "Top": ["H&M", "Zara", "Uniqlo", "Gap", "J.Crew"],
        "Bottom": ["Levi's", "H&M", "American Eagle", "Gap", "Uniqlo"],
        "Dress": ["Zara", "H&M", "Mango", "ASOS", "Forever 21"],
        "Shoes": ["Nike", "Adidas", "Vans", "Converse", "New Balance"],
        "Accessory": ["Fossil", "Mango", "Zara", "H&M", "ASOS"],
        "Outerwear": ["North Face", "Columbia", "Patagonia", "Uniqlo", "Gap"],
    }
    
    # Select a brand based on category
    category_key = next((k for k in brands.keys() if k.lower() in category.lower()), "Top")
    brand = random.choice(brands.get(category_key, ["Fashion Brand"]))
    
    # Create a product name
    color_prefix = f"{color} " if color else ""
    name = f"{color_prefix}{description if description else category}"
    
    # Default fallback image URLs by category
    default_images = {
        "Top": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=600",
        "Bottom": "https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?w=600",
        "Dress": "https://images.unsplash.com/photo-1496747611176-843222e1e57c?w=600",
        "Shoes": "https://images.unsplash.com/photo-1560343090-f0409e92791a?w=600",
        "Accessory": "https://images.unsplash.com/photo-1608042314453-ae338d80c427?w=600",
        "Outerwear": "https://images.unsplash.com/photo-1539533113208-f6df8cc8b543?w=600",
    }
    
    # Get appropriate image URL
    image_key = next((k for k in default_images.keys() if k.lower() in category.lower()), "Top")
    image_url = default_images.get(image_key)
    
    return {
        "name": name,
        "brand": brand,
        "image_url": image_url
    }

# Routes
@router.post("/generate", response_model=OutfitGenerateResponse)
async def generate_outfit(request: OutfitGenerateRequest) -> OutfitGenerateResponse:
    """
    Generate outfit recommendations based on user request, with better separation
    of concept generation and product matching.
    
    Args:
        request: The outfit generation request containing prompt, gender, budget
        
    Returns:
        OutfitGenerateResponse: The generated outfits with concepts and matched products
    """
    logger.info(f"Generating outfit for prompt: {request.prompt}, gender: {request.gender}, budget: {request.budget}")
    
    try:
        # Step 1: Generate outfit concepts with Claude
        outfit_concepts = await generate_outfit_concepts(request)
        
        # Step 2: Try to match real products to concepts (but this is optional)
        enhanced_outfits = await enhance_outfits_with_products(outfit_concepts, request)
        
        # Create the response using the enhanced outfits
        return OutfitGenerateResponse(
            outfits=enhanced_outfits,
            prompt=request.prompt
        )
        
    except Exception as e:
        logger.error(f"Error in outfit generation pipeline: {str(e)}", exc_info=True)
        # Fall back to mock data, but clearly mark it as a fallback
        fallback_outfits = get_mock_outfits()
        for outfit in fallback_outfits:
            outfit.description = f"[FALLBACK OUTFIT] {outfit.description}"
        
        return OutfitGenerateResponse(
            outfits=fallback_outfits,
            prompt=request.prompt
        )

# Add alias route for AI-generate that calls the same function
@router.post("/ai-generate", response_model=OutfitGenerateResponse)
async def ai_generate_outfit(request: OutfitGenerateRequest):
    """Alias for generate_outfit - used by frontend"""
    return await generate_outfit(request)

@router.get("/trending", response_model=Dict[str, Dict[str, List[str]]])
async def get_trending_styles():
    """Get trending style keywords for outfit generation"""
    try:
        # In a real implementation, this would come from a database or analytics
        # For now, we'll return mock data
        styles = {
            "casual": ["Everyday Basics", "Streetwear", "Athleisure"],
            "formal": ["Business Casual", "Office Wear", "Evening Elegance"],
            "seasonal": ["Summer Vibes", "Fall Layers", "Winter Chic"],
            "trending": ["Y2K Revival", "Coastal Grandmother", "Quiet Luxury", "Dark Academia", "Festival Style", "Coachella", "Bohemian"]
        }
        
        return {"styles": styles}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get trending styles: {str(e)}")

@router.get("/test_serpapi", include_in_schema=False)
async def test_serpapi(query: str, category: Optional[str] = None, gender: str = "female"):
    """Test endpoint for SerpAPI product search"""
    try:
        logger.info(f"Testing SerpAPI search for: {query} in category {category}")
        products = serpapi_service.search_products(
            query=query,
            category=category or "Top",
            gender=gender,
            limit=5
        )
        return {"products": products, "count": len(products)}
    except Exception as e:
        logger.error(f"Error testing SerpAPI: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error testing SerpAPI: {str(e)}")

# --- DEBUGGING ENDPOINT --- 
@router.get("/debug-mock", response_model=List[Outfit], include_in_schema=False) # Return list of Outfit models
async def debug_mock_outfits():
    """Directly returns the output of get_mock_outfits for debugging."""
    logger.info("Accessing /debug-mock endpoint.")
    try:
        mock_data = get_mock_outfits()
        # Ensure the data matches the Outfit model (already done inside get_mock_outfits likely)
        # Convert raw dicts to Pydantic models if necessary, though get_mock_outfits might already return them
        # For simplicity, assume get_mock_outfits returns data suitable for direct return if response_model=List[Outfit]
        logger.info(f"Returning {len(mock_data)} mock outfits from debug endpoint.")
        return mock_data 
    except Exception as e:
        logger.error(f"Error in /debug-mock endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error fetching debug mock data")
# --- END DEBUGGING ENDPOINT --- 

@router.get("/debug_serpapi", include_in_schema=False)  # Changed dash to underscore and added include_in_schema
async def debug_serpapi():
    """Debug endpoint to check SerpAPI configuration"""
    import os
    from dotenv import load_dotenv
    
    # Try to reload environment variables
    load_dotenv()
    
    # Check if SERPAPI_KEY is in environment variables
    serpapi_key = os.getenv("SERPAPI_KEY")
    masked_key = serpapi_key[:4] + "..." + serpapi_key[-4:] if serpapi_key and len(serpapi_key) > 8 else None
    
    # Check if the key exists in a secret file
    secret_file_exists = os.path.exists("/etc/secrets/SERPAPI_KEY")
    secret_file_content = None
    if secret_file_exists:
        try:
            with open("/etc/secrets/SERPAPI_KEY", "r") as f:
                secret_content = f.read().strip()
                secret_file_content = secret_content[:4] + "..." + secret_content[-4:] if len(secret_content) > 8 else "***"
        except Exception as e:
            secret_file_content = f"Error reading: {str(e)}"
    
    # Get the service's API key
    from app.services.serpapi_service import serpapi_service
    service_key = serpapi_service.api_key
    masked_service_key = service_key[:4] + "..." + service_key[-4:] if service_key and len(service_key) > 8 else None
    
    # Test a real API call
    try:
        results = serpapi_service.search_products(
            query="blue jeans",
            category="Bottom",
            gender="unisex",
            limit=1
        )
        api_working = not any("fallback" in result.get("product_id", "") for result in results)
        first_result = results[0] if results else None
        is_fallback = "fallback" in first_result.get("product_id", "") if first_result else True
    except Exception as e:
        api_working = False
        first_result = str(e)
        is_fallback = True
    
    return {
        "environment_key": masked_key is not None,
        "environment_key_value": masked_key,
        "secret_file_exists": secret_file_exists,
        "secret_file_content": secret_file_content,
        "service_key": masked_service_key is not None,
        "service_key_value": masked_service_key,
        "api_working": api_working,
        "is_fallback": is_fallback,
        "first_result_type": type(first_result).__name__,
        "first_result": {k: v for k, v in first_result.items()} if isinstance(first_result, dict) else str(first_result)
    }

# New debug endpoint with a distinct path that won't conflict with others
@router.get("/debug/serpapi/config", include_in_schema=False)
async def debug_serpapi_config():
    """Debug endpoint to check SerpAPI configuration (alternative path)"""
    import os
    from dotenv import load_dotenv
    
    # Try to reload environment variables
    load_dotenv()
    
    # Check if SERPAPI_KEY is in environment variables
    serpapi_key = os.getenv("SERPAPI_KEY")
    masked_key = serpapi_key[:4] + "..." + serpapi_key[-4:] if serpapi_key and len(serpapi_key) > 8 else None
    
    # Check if the key exists in a secret file
    secret_file_exists = os.path.exists("/etc/secrets/SERPAPI_KEY")
    secret_file_content = None
    if secret_file_exists:
        try:
            with open("/etc/secrets/SERPAPI_KEY", "r") as f:
                secret_content = f.read().strip()
                secret_file_content = secret_content[:4] + "..." + secret_content[-4:] if len(secret_content) > 8 else "***"
        except Exception as e:
            secret_file_content = f"Error reading: {str(e)}"
    
    # Get the service's API key
    from app.services.serpapi_service import serpapi_service
    service_key = serpapi_service.api_key
    masked_service_key = service_key[:4] + "..." + service_key[-4:] if service_key and len(service_key) > 8 else None
    
    # Test a real API call
    try:
        results = serpapi_service.search_products(
            query="blue jeans",
            category="Bottom",
            gender="unisex",
            limit=1
        )
        api_working = not any("fallback" in result.get("product_id", "") for result in results)
        first_result = results[0] if results else None
        is_fallback = "fallback" in first_result.get("product_id", "") if first_result else True
    except Exception as e:
        api_working = False
        first_result = str(e)
        is_fallback = True
    
    return {
        "environment_key": masked_key is not None,
        "environment_key_value": masked_key,
        "secret_file_exists": secret_file_exists,
        "secret_file_content": secret_file_content,
        "service_key": masked_service_key is not None,
        "service_key_value": masked_service_key,
        "api_working": api_working,
        "is_fallback": is_fallback,
        "first_result_type": type(first_result).__name__,
        "first_result": {k: v for k, v in first_result.items()} if isinstance(first_result, dict) else str(first_result)
    }

@router.get("/{outfit_id}", response_model=Outfit)
async def get_outfit(outfit_id: str):
    """Get outfit details by ID"""
    try:
        outfits = get_mock_outfits()
        outfit = next((o for o in outfits if o["id"] == outfit_id), None)
        
        if not outfit:
            raise HTTPException(status_code=404, detail=f"Outfit with ID {outfit_id} not found")
        
        return Outfit(**outfit)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get outfit: {str(e)}")

# New test endpoint with a simple response
@router.get("/test/simple")
async def test_simple():
    """Simple test endpoint that returns a basic response"""
    return {"status": "ok", "message": "Simple test endpoint working"}

# Fully independent debug test endpoint that doesn't rely on any external resource
@router.get("/debug-test")
async def debug_test():
    """A completely independent test endpoint that returns hardcoded data without external dependencies"""
    return {
        "status": "ok",
        "message": "Debug test endpoint working correctly",
        "serpapi_config": {
            "fixed": True,
            "using_settings": False,
            "cache_ttl": 604800,  # 7 days
            "retry_strategy": "exponential_backoff"
        }
    } 