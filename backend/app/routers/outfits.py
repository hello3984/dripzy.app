from fastapi import APIRouter, HTTPException, Depends, Query, Body
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os
import json
import random
import logging # Added logging
import re
import uuid
from datetime import datetime

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

async def _find_products_for_item(query: str, category: str, 
                           gender: Optional[str] = None, 
                           budget: Optional[float] = None,
                           include_alternatives: bool = True,
                           alternatives_count: int = 5) -> List[Dict[str, Any]]:
    """
    Find products matching an item description, including alternatives.
    
    Args:
        query: Search query built from keywords/description
        category: Item category
        gender: Gender preference
        budget: Budget constraint
        include_alternatives: Whether to include alternative products
        alternatives_count: Number of alternatives to include
        
    Returns:
        List of matching products (main result plus alternatives)
    """
    try:
        # Calculate price range based on budget and category
        min_price, max_price = None, None
        if budget:
            if category in ["Outerwear", "Dress"]:
                max_price = budget * 0.5  # These can be up to 50% of total budget
            elif category == "Shoes":
                max_price = budget * 0.3  # Shoes up to 30% of budget
            elif category in ["Top", "Bottom"]:
                max_price = budget * 0.25  # Basic clothing up to 25% of budget
            elif category == "Accessory":
                max_price = budget * 0.15  # Accessories up to 15% of budget
        
        # Request limit includes main product + alternatives
        search_limit = alternatives_count + 1 if include_alternatives else 1
        
        # Search for products using SerpAPI service
        products = await serpapi_service.search_products(
            query=query,
            category=category,
            gender=gender,
            limit=search_limit,
            min_price=min_price,
            max_price=max_price
        )
        
        return products
    except Exception as e:
        logger.error(f"Error finding products for {category} - {query}: {str(e)}")
        return [] 

async def enhance_outfits_with_products(outfit_concepts: List[Dict[str, Any]], 
                                  request: OutfitGenerateRequest) -> List[Outfit]:
    """
    Try to enhance outfit concepts with real product matches, but prioritize
    the concept even if products can't be found.
    
    Args:
        outfit_concepts: Concepts generated by Claude
        request: Original user request
        
    Returns:
        List of Outfit objects with products matched where possible
    """
    enhanced_outfits = []
    
    for concept in outfit_concepts:
        try:
            # Create a unique ID for the outfit
            outfit_id = str(uuid.uuid4())
            
            # Extract basic outfit information
            outfit_name = concept.get("outfit_name", "Stylish Outfit")
            outfit_description = concept.get("description", "A stylish outfit recommendation")
            outfit_style = concept.get("style", _determine_style(outfit_name, outfit_description, request.prompt))
            outfit_occasion = concept.get("occasion", "Casual")
            
            # Try to match products for each item, but don't break if we can't find matches
            outfit_items = []
            total_price = 0
            brand_display = {}
            
            # Process each conceptual item and try to match real products
            for item_concept in concept.get("items", []):
                # Get search info
                category = item_concept.get("category")
                description = item_concept.get("description", "")
                search_keywords = item_concept.get("search_keywords", [])
                
                # Build search query from keywords and description
                search_query = " ".join(search_keywords) if search_keywords else description
                
                try:
                    # Try to find matching products, including alternatives if requested
                    products = await _find_products_for_item(
                        search_query, 
                        category, 
                        request.gender, 
                        request.budget,
                        include_alternatives=request.include_alternatives
                    )
                    
                    if products:
                        # First product is the main match
                        main_product = products[0]
                        
                        # Remaining products are alternatives (if any)
                        alternatives = products[1:] if len(products) > 1 else []
                        
                        # Create OutfitItem from the main product
                        outfit_item = OutfitItem(
                            product_id=main_product.get("product_id", ""),
                            product_name=main_product.get("product_name", item_concept.get("description", "")),
                            brand=main_product.get("brand", "Various"),
                            category=category,
                            price=main_product.get("price", 0.0),
                            url=main_product.get("url", ""),
                            image_url=main_product.get("image_url", ""),
                            description=main_product.get("description", ""),
                            concept_description=item_concept.get("description", ""),
                            color=item_concept.get("color", ""),
                            alternatives=alternatives,
                            is_fallback=False
                        )
                        
                        # Update running data
                        outfit_items.append(outfit_item)
                        total_price += outfit_item.price
                        
                        # Track brand for display
                        if outfit_item.brand:
                            brand_display[outfit_item.brand] = main_product.get("image_url", "")
                    else:
                        # If no product match, still include the concept item with fallback flag
                        outfit_item = OutfitItem(
                            product_id=f"concept_{uuid.uuid4().hex[:8]}",
                            product_name=f"{category}: {description}",
                            brand="Concept Only",
                            category=category,
                            price=0.0,
                            url="",
                            image_url=f"https://via.placeholder.com/300x400?text={category}",
                            description=description,
                            concept_description=description,
                            color=item_concept.get("color", ""),
                            alternatives=[],
                            is_fallback=True
                        )
                        outfit_items.append(outfit_item)
                        
                except Exception as item_error:
                    # Log but continue with other items
                    logger.error(f"Error matching products for {category}: {str(item_error)}")
                    # Still include the concept item
                    outfit_item = OutfitItem(
                        product_id=f"concept_{uuid.uuid4().hex[:8]}",
                        product_name=f"{category}: {description}",
                        brand="Concept Only",
                        category=category,
                        price=0.0,
                        url="",
                        image_url=f"https://via.placeholder.com/300x400?text={category}",
                        description=description,
                        concept_description=description,
                        color=item_concept.get("color", ""),
                        alternatives=[],
                        is_fallback=True
                    )
                    outfit_items.append(outfit_item)
            
            # Create outfit with available items
            outfit = Outfit(
                id=outfit_id,
                name=outfit_name,
                description=outfit_description,
                style=outfit_style,
                occasion=outfit_occasion,
                items=outfit_items,
                total_price=total_price,
                brand_display=brand_display,
                stylist_rationale=concept.get("stylist_rationale", "A stylish outfit recommendation")
            )
            
            # Generate collage if we have images
            if outfit_items:
                try:
                    await _add_collage_to_outfit(outfit)
                except Exception as collage_error:
                    logger.error(f"Error creating collage: {str(collage_error)}")
            
            enhanced_outfits.append(outfit)
            
        except Exception as outfit_error:
            logger.error(f"Error enhancing outfit: {str(outfit_error)}")
    
    # If no outfits could be processed, use mock outfit as fallback
    if not enhanced_outfits:
        logger.warning("No outfits could be enhanced. Using fallback mockups.")
        return get_mock_outfits()
    
    return enhanced_outfits 

# Add new endpoint to get alternatives for an item
@router.get("/alternatives/{item_id}", response_model=List[Dict[str, Any]])
async def get_item_alternatives(item_id: str):
    """
    Get alternative products for a specific outfit item.
    
    Args:
        item_id: The ID of the outfit item
        
    Returns:
        List of alternative products
    """
    try:
        logger.info(f"Fetching alternatives for item ID: {item_id}")
        
        # Check cache for alternatives
        cache_key = f"alternatives_{item_id}"
        cached_alternatives = cache_service.get(cache_key, "medium")
        
        if cached_alternatives:
            logger.info(f"Using cached alternatives for item {item_id}")
            return cached_alternatives
        
        # If not in cache, find the outfit item in stored outfits 
        # This would work better with a database, but we'll use our in-memory cache for now
        
        # First get all outfits from cache
        outfit_keys = [key for key in cache_service._cache.keys() if key.startswith("outfit_")]
        
        # Search through outfits for the item
        for key in outfit_keys:
            outfit_data = cache_service.get(key, "medium")
            if not outfit_data:
                continue
                
            # Search through items in each outfit
            for outfit in outfit_data.get("outfits", []):
                for item in outfit.get("items", []):
                    if item.get("product_id") == item_id:
                        logger.info(f"Found item {item_id} in outfit {outfit.get('id')}")
                        alternatives = item.get("alternatives", [])
                        
                        # If item has alternatives, return them
                        if alternatives:
                            cache_service.set(cache_key, alternatives, "medium")
                            return alternatives
                        
                        # If no stored alternatives, try to fetch new ones
                        try:
                            category = item.get("category")
                            description = item.get("concept_description") or item.get("description", "")
                            
                            # Generate new alternatives
                            new_alternatives = await _find_products_for_item(
                                description,
                                category,
                                include_alternatives=True,
                                alternatives_count=8  # Get more alternatives when explicitly requested
                            )
                            
                            # Remove the original item from alternatives if present
                            new_alternatives = [p for p in new_alternatives 
                                              if p.get("product_id") != item_id]
                            
                            # Cache and return alternatives
                            cache_service.set(cache_key, new_alternatives, "medium")
                            return new_alternatives
                            
                        except Exception as e:
                            logger.error(f"Error generating alternatives: {str(e)}")
                            return []
        
        # If we get here, item not found
        logger.warning(f"Item ID {item_id} not found in any stored outfit")
        raise HTTPException(status_code=404, detail=f"Item with ID {item_id} not found")
            
    except Exception as e:
        logger.error(f"Error fetching alternatives: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch alternatives: {str(e)}")

# Add endpoint to replace an item in an outfit with an alternative
@router.post("/replace-item/{outfit_id}/{item_id}")
async def replace_item_with_alternative(
    outfit_id: str, 
    item_id: str, 
    alternative_id: str = Body(..., embed=True)
):
    """
    Replace an item in an outfit with one of its alternatives.
    
    Args:
        outfit_id: ID of the outfit
        item_id: ID of the item to replace
        alternative_id: ID of the alternative product to use as replacement
        
    Returns:
        Updated outfit
    """
    try:
        logger.info(f"Replacing item {item_id} with alternative {alternative_id} in outfit {outfit_id}")
        
        # Find the outfit in our cache
        cache_key = f"outfit_{outfit_id}"
        outfit_data = cache_service.get(cache_key, "medium")
        
        if not outfit_data:
            raise HTTPException(status_code=404, detail=f"Outfit with ID {outfit_id} not found")
            
        # Find the item and alternative
        found = False
        outfit = None
        
        for outfit_obj in outfit_data.get("outfits", []):
            if outfit_obj.get("id") == outfit_id:
                outfit = outfit_obj
                
                # Find the item to replace
                for i, item in enumerate(outfit.get("items", [])):
                    if item.get("product_id") == item_id:
                        # Find the alternative in item's alternatives
                        for alt in item.get("alternatives", []):
                            if alt.get("product_id") == alternative_id:
                                # Create a new item from the alternative
                                new_item = OutfitItem(
                                    product_id=alt.get("product_id", ""),
                                    product_name=alt.get("product_name", ""),
                                    brand=alt.get("brand", "Various"),
                                    category=item.get("category"),  # Keep the same category
                                    price=alt.get("price", 0.0),
                                    url=alt.get("url", ""),
                                    image_url=alt.get("image_url", ""),
                                    description=alt.get("description", ""),
                                    concept_description=item.get("concept_description", ""),  # Keep original concept
                                    color=alt.get("color", item.get("color", "")),
                                    alternatives=item.get("alternatives", []),  # Keep same alternatives list
                                    is_fallback=False
                                )
                                
                                # Replace item in outfit
                                outfit["items"][i] = new_item.dict()
                                
                                # Recalculate total price
                                outfit["total_price"] = sum(item.get("price", 0) for item in outfit["items"])
                                
                                # Update brand display if needed
                                if outfit.get("brand_display") and new_item.brand:
                                    outfit["brand_display"][new_item.brand] = new_item.image_url
                                
                                found = True
                                break
                        
                        # If alternative not found
                        if not found:
                            raise HTTPException(
                                status_code=404, 
                                detail=f"Alternative with ID {alternative_id} not found for item {item_id}"
                            )
                break
        
        if not found:
            raise HTTPException(status_code=404, detail=f"Item with ID {item_id} not found in outfit {outfit_id}")
            
        # Update cache with modified outfit
        cache_service.set(cache_key, outfit_data, "medium")
        
        # Update collage image with new product
        try:
            if outfit:
                items = [OutfitItem(**item) for item in outfit.get("items", [])]
                outfit_obj = Outfit(
                    id=outfit.get("id"),
                    name=outfit.get("name"),
                    description=outfit.get("description"),
                    style=outfit.get("style"),
                    occasion=outfit.get("occasion", "casual"),
                    items=items,
                    total_price=outfit.get("total_price", 0.0),
                    brand_display=outfit.get("brand_display", {})
                )
                await _add_collage_to_outfit(outfit_obj)
                
                # Update outfit with new collage
                outfit["collage_url"] = outfit_obj.collage_url
        except Exception as collage_error:
            logger.error(f"Error updating collage after replacement: {str(collage_error)}")
        
        return Response(status_code=200, content=json.dumps({"status": "success", "outfit": outfit}))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error replacing item: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to replace item: {str(e)}") 

@router.get("/debug/check-serpapi", response_model=Dict[str, Any])
async def debug_check_serpapi():
    """
    Debug endpoint to test if SerpAPI key is valid and working.
    """
    logger.info("Checking SerpAPI key validity")
    
    # Test if the SerpAPI key is valid
    is_valid = await serpapi_service.test_api_key()
    
    return {
        "status": "ok" if is_valid else "error",
        "message": "SerpAPI key is valid" if is_valid else "SerpAPI key is invalid or not configured",
        "api_key_configured": serpapi_service.api_key is not None,
        "timestamp": datetime.now().isoformat()
    } 