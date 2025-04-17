from fastapi import APIRouter, HTTPException, Depends, Query, Body, Response, Request, status, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os
import json
import random
import logging
import re
import uuid
from datetime import datetime
import asyncio
import time
import aiohttp

# --- Added Imports ---
import anthropic
from dotenv import load_dotenv
from app.services.image_service import create_outfit_collage
from app.services.serpapi_service import SerpAPIService
from app.utils.image_processing import create_brand_display
from app.models.outfit_models import OutfitItem, Outfit, OutfitGenerateRequest, OutfitGenerateResponse
from app.core.cache import cache_service
from app.core.config import settings
from app.dependencies import get_db
from app.services.search_optimizer import get_search_optimizer

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
    """Get mock outfits for demo purposes (simplified version)"""
    logger = logging.getLogger(__name__)
    logger.warning("Using minimal mock outfits instead of real data")
    
    # Return a minimal outfit to avoid cluttering the UI
    return [
        {
            "id": "mock-outfit",
            "name": "Example Outfit",
            "description": "This is a placeholder outfit. Real data will be shown when API connection is restored.",
            "style": "simple",
            "occasion": "casual",
            "total_price": 99.99,
            "items": [
                {
                    "product_id": "mock-item",
                    "product_name": "Example Item",
                    "brand": "Example Brand",
                    "category": "tops",
                    "price": 29.99,
                    "url": "",
                    "image_url": "https://via.placeholder.com/300x400?text=No+Image",
                    "description": "This is a placeholder item.",
                    "concept_description": "Basic item",
                    "color": "neutral",
                    "alternatives": [],
                    "is_fallback": True
                }
            ],
            "image_url": None,
            "collage_url": None,
            "brand_display": {},
            "stylist_rationale": "Placeholder outfit while API connection is being established."
        }
    ]

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

# --- Added Missing Functions ---

async def generate_outfit_concepts(request: OutfitGenerateRequest) -> List[Dict[str, Any]]:
    """
    Generate outfit concepts using Claude AI.
    
    Args:
        request: The outfit generation request with prompt, gender, budget
        
    Returns:
        List of outfit concepts with detailed item descriptions
    """
    cache_key = f"outfit_concepts:{request.prompt}:{request.gender}:{request.budget}"
    cached_concepts = cache_service.get(cache_key)
    if cached_concepts:
        logger.info(f"Using cached outfit concepts for: {request.prompt}")
        return cached_concepts
    
    # Don't proceed without API key and client
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    logger.info(f"ANTHROPIC_API_KEY status: {'Found' if api_key else 'Missing'}")
    if not api_key:
        logger.error("Missing ANTHROPIC_API_KEY environment variable")
        return []
    
    if not anthropic_client:
        logger.error("Anthropic client not initialized")
        return []
    
    # Prepare for retry logic
    max_attempts = 3
    backoff_time = 1  # Start with 1 second backoff
    
    prompt_base = f"""
You are a fashion stylist assistant creating outfits for a customer based on their needs.

### Customer Request
I am looking for outfit ideas for: {request.prompt}
Gender: {request.gender if request.gender else 'Any'}
Budget: {'$' + str(request.budget) if request.budget else 'Any budget'}

### Task
I need you to generate {request.num_outfits or 3} unique outfit concepts suitable for this request.
For each outfit, include the following:
- outfit_name: A catchy name for the outfit
- description: A brief description of the overall look and feel
- style: The primary style category (e.g. casual, formal, bohemian)
- occasion: When this outfit would be appropriate to wear
- stylist_rationale: Why this outfit works for the request
- items: An array of clothing/accessory items that make up the outfit (4-7 items per outfit)

For each item in the outfit, include:
- category: The specific category (e.g. "jeans", "t-shirt", "sneakers", "handbag")
- description: Detailed description of the item
- color: The main color of the item
- search_keywords: Array of 3-5 search terms that would help find this specific item online

OUTPUT FORMAT: Your entire response must be valid JSON with this structure:
[
  {{
    "outfit_name": "Example Outfit",
    "description": "A stylish ensemble perfect for...",
    "style": "casual",
    "occasion": "everyday",
    "stylist_rationale": "This outfit works because...",
    "items": [
      {{
        "category": "jeans",
        "description": "High-waisted straight leg jeans",
        "color": "blue",
        "search_keywords": ["high waisted", "straight leg", "denim", "jeans"]
      }},
      // more items...
    ]
  }},
  // more outfits...
]

IMPORTANT: Make sure your response is ONLY valid JSON without any other text.
"""

    for attempt in range(max_attempts):
        try:
            logger.info(f"Calling Claude API (attempt {attempt+1}/{max_attempts})")
            start_time = time.time()
            
            response = await anthropic_client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=2000,
                temperature=0.7,
                system="You are a fashion stylist specialist who creates detailed outfit recommendations.",
                messages=[
                    {"role": "user", "content": prompt_base}
                ]
            )
            
            elapsed = time.time() - start_time
            logger.info(f"Claude API response received in {elapsed:.2f}s")
            
            if not response.content:
                logger.warning("Empty response from Claude API")
                continue
                
            # Extract content from response
            text_content = response.content[0].text
            
            # Extract JSON from the response
            outfit_concepts = extract_json_from_text(text_content)
            
            if outfit_concepts and isinstance(outfit_concepts, list) and len(outfit_concepts) > 0:
                logger.info(f"Successfully extracted {len(outfit_concepts)} outfit concepts")
                cache_service.set(cache_key, outfit_concepts)
                return outfit_concepts
            else:
                logger.warning(f"Failed to extract valid outfit concepts JSON (attempt {attempt+1})")
        
        except Exception as e:
            logger.error(f"Error calling Claude API (attempt {attempt+1}): {str(e)}")
        
        # If we got here, the attempt failed
        if attempt < max_attempts - 1:
            logger.info(f"Retrying in {backoff_time} seconds...")
            await asyncio.sleep(backoff_time)
            backoff_time *= 2  # Exponential backoff
    
    logger.error(f"All {max_attempts} attempts to generate outfit concepts failed")
    return []


def extract_json_from_text(text: str) -> Optional[List[Dict[str, Any]]]:
    """
    Extract JSON from text returned by Claude.
    
    This handles several common response formats:
    1. Clean JSON with no surrounding text
    2. JSON with markdown code fences
    3. JSON embedded in regular text
    
    Args:
        text: The text response from Claude
        
    Returns:
        Parsed JSON object or None if extraction failed
    """
    # Case 1: Try direct JSON parsing first
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list) and len(parsed) > 0:
            return parsed
    except json.JSONDecodeError:
        pass
    
    # Case 2: Try to extract from markdown code blocks
    code_block_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
    code_blocks = re.findall(code_block_pattern, text)
    
    for block in code_blocks:
        try:
            parsed = json.loads(block)
            if isinstance(parsed, list) and len(parsed) > 0:
                return parsed
        except json.JSONDecodeError:
            continue
    
    # Case 3: Try to extract JSON array from anywhere in the text
    try:
        # Find the outermost array brackets
        array_start = text.find('[')
        if array_start >= 0:
            # Find the matching closing bracket
            brace_count = 0
            for i in range(array_start, len(text)):
                if text[i] == '[':
                    brace_count += 1
                elif text[i] == ']':
                    brace_count -= 1
                    if brace_count == 0:
                        # Found the end of the array
                        json_str = text[array_start:i+1]
                        parsed = json.loads(json_str)
                        if isinstance(parsed, list) and len(parsed) > 0:
                            return parsed
                        break
    except (json.JSONDecodeError, ValueError, IndexError):
        pass
    
    # Final attempt: Just try to find any valid JSON array anywhere
    try:
        # Extract anything that looks like JSON array
        array_pattern = r"\[(.*)\]"
        match = re.search(array_pattern, text, re.DOTALL)
        if match:
            json_str = f"[{match.group(1)}]"
            parsed = json.loads(json_str)
            if isinstance(parsed, list) and len(parsed) > 0:
                return parsed
    except (json.JSONDecodeError, IndexError):
        pass
    
    logger.error("Could not extract valid JSON from response")
    return None

def _determine_style(outfit_name: str, outfit_description: str, user_prompt: str) -> str:
    """Determine outfit style based on keywords if not provided."""
    text_content = f"{outfit_name} {outfit_description} {user_prompt}".lower()
    # Simple heuristic, can be expanded
    if "formal" in text_content or "business" in text_content or "evening" in text_content:
        return "Formal"
    if "streetwear" in text_content or "urban" in text_content:
        return "Streetwear"
    if "bohemian" in text_content or "festival" in text_content:
        return "Bohemian"
    # Add more style checks as needed
    return "Casual" # Default

def _add_collage_to_outfit(outfit: Outfit):
    """Generate and add a collage URL to the outfit object."""
    image_urls = [item.image_url for item in outfit.items if item.image_url]
    if len(image_urls) >= 2: # Need at least 2 images for a collage
        try:
            collage_url = create_outfit_collage(image_urls, outfit.id)
            outfit.collage_url = collage_url
            logger.info(f"Collage created for outfit {outfit.id}: {collage_url}")
        except Exception as e:
            logger.error(f"Failed to create collage for outfit {outfit.id}: {str(e)}")
    else:
        logger.warning(f"Not enough images ({len(image_urls)}) to create collage for outfit {outfit.id}")

# --- End Added Missing Functions ---

# Routes
@router.post("/generate", response_model=OutfitGenerateResponse)
async def generate_outfit(request: OutfitGenerateRequest) -> OutfitGenerateResponse:
    """
    Generate outfit recommendations based on user request.
    
    Args:
        request: The outfit generation request containing prompt, gender, budget
        
    Returns:
        OutfitGenerateResponse: The generated outfits with concepts and matched products
    """
    logger.info(f"Generating outfit for prompt: {request.prompt}, gender: {request.gender}, budget: {request.budget}")
    
    # Check the cache first
    cache_key = f"outfit_response:{request.prompt}:{request.gender}:{request.budget}"
    cached_response = cache_service.get(cache_key, "long")
    if cached_response:
        logger.info(f"Using cached outfit response for: {request.prompt}")
        return OutfitGenerateResponse(**cached_response)
    
    try:
        # Step 1: Generate outfit concepts with Claude
        logger.info("Generating outfit concepts with Claude")
        outfit_concepts = await generate_outfit_concepts(request)
        
        # Handle case where concept generation failed
        if not outfit_concepts:
            logger.warning("Outfit concept generation failed. Using fallback mockups.")
            return OutfitGenerateResponse(outfits=get_mock_outfits(), prompt=request.prompt)

        # Step 2: Match products to concepts
        logger.info(f"Enhancing {len(outfit_concepts)} outfit concepts with real products")
        enhanced_outfits = await enhance_outfits_with_products(outfit_concepts, request)
        
        # Create the response
        response = OutfitGenerateResponse(
            outfits=enhanced_outfits,
            prompt=request.prompt
        )
        
        # Cache successful response
        cache_service.set(cache_key, response.dict(), "long")
        
        return response
        
    except Exception as e:
        logger.error(f"Error in outfit generation: {str(e)}", exc_info=True)
        # Fall back to mock data with error message
        fallback_outfits = get_mock_outfits()
        for outfit in fallback_outfits:
            outfit['description'] = f"[ERROR] {outfit.get('description', 'Mock outfit')}" 
        
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
async def test_serpapi(query: str, category: Optional[str] = None):
    """Test endpoint for SerpAPI product search"""
    try:
        logger.info(f"Testing SerpAPI search for: {query} in category {category}")
        # Get service instance correctly
        serpapi_service_instance = get_serpapi_service()
        # Call method on the instance, remove invalid args
        products = await serpapi_service_instance.search_products(
            query=query,
            category=category or "Top"
            # Removed gender and limit arguments
        )
        return {"products": products, "count": len(products)}
    except Exception as e:
        logger.error(f"Error testing SerpAPI: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error testing SerpAPI: {str(e)}")

# --- DEBUGGING ENDPOINT --- 
@router.get("/debug-mock", response_model=List[Outfit])
async def debug_mock_outfits():
    """Directly returns the output of get_mock_outfits for debugging."""
    logger.info("Accessing /debug-mock endpoint.")
    try:
        # Get the mock outfits directly
        mock_data = get_mock_outfits()
        
        # Convert any dict items to Outfit models if needed
        outfits = []
        for outfit in mock_data:
            if isinstance(outfit, dict):
                outfits.append(Outfit(**outfit))
            else:
                outfits.append(outfit)
                
        logger.info(f"Returning {len(outfits)} mock outfits from debug endpoint.")
        return outfits
    except Exception as e:
        logger.error(f"Error in /debug-mock endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching debug mock data: {str(e)}")
# --- END DEBUGGING ENDPOINT --- 

@router.get("/debug_serpapi", include_in_schema=False)  # Changed dash to underscore and added include_in_schema
async def debug_serpapi():
    """Debug endpoint to check SerpAPI configuration"""
    import os
    from dotenv import load_dotenv
    
    # Try to reload environment variables
    load_dotenv()
    
    # Check if SERPAPI_API_KEY is in environment variables
    serpapi_key = os.getenv("SERPAPI_API_KEY")
    masked_key = serpapi_key[:4] + "..." + serpapi_key[-4:] if serpapi_key and len(serpapi_key) > 8 else None
    
    # Check if the key exists in a secret file
    secret_file_exists = os.path.exists("/etc/secrets/SERPAPI_API_KEY")
    secret_file_content = None
    if secret_file_exists:
        try:
            with open("/etc/secrets/SERPAPI_API_KEY", "r") as f:
                secret_content = f.read().strip()
                secret_file_content = secret_content[:4] + "..." + secret_content[-4:] if len(secret_content) > 8 else "***"
        except Exception as e:
            secret_file_content = f"Error reading: {str(e)}"
    
    # Get the service's API key using the correct method
    serpapi_service_instance = get_serpapi_service() # Get instance
    service_key = serpapi_service_instance.api_key
    masked_service_key = service_key[:4] + "..." + service_key[-4:] if service_key and len(service_key) > 8 else None
    
    # Test a real API call using the instance
    try:
        results = await serpapi_service_instance.search_products(
            query="blue jeans",
            category="Bottom"
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
    
    # Check if SERPAPI_API_KEY is in environment variables
    serpapi_key = os.getenv("SERPAPI_API_KEY")
    masked_key = serpapi_key[:4] + "..." + serpapi_key[-4:] if serpapi_key and len(serpapi_key) > 8 else None
    
    # Check if the key exists in a secret file
    secret_file_exists = os.path.exists("/etc/secrets/SERPAPI_API_KEY")
    secret_file_content = None
    if secret_file_exists:
        try:
            with open("/etc/secrets/SERPAPI_API_KEY", "r") as f:
                secret_content = f.read().strip()
                secret_file_content = secret_content[:4] + "..." + secret_content[-4:] if len(secret_content) > 8 else "***"
        except Exception as e:
            secret_file_content = f"Error reading: {str(e)}"
    
    # Get the service's API key using the correct method
    serpapi_service_instance = get_serpapi_service() # Get instance
    service_key = serpapi_service_instance.api_key
    masked_service_key = service_key[:4] + "..." + service_key[-4:] if service_key and len(service_key) > 8 else None
    
    # Test a real API call using the instance
    try:
        results = await serpapi_service_instance.search_products(
            query="blue jeans",
            category="Bottom"
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
    """Debug test endpoint"""
    try:
        data = {"message": "Debug test endpoint working", "success": True}
        return data
    except Exception as e:
        logger.error(f"Error in debug test: {e}")
        return {"error": str(e)}

# --- Dependency Function ---
def get_serpapi_service() -> SerpAPIService:
    # Ensure the service is created with the key from settings
    return SerpAPIService(settings=settings)

# --- Updated Function Signatures to use Depends --- 

# Removed dependency injection from signature
async def _find_products_for_item(query: str, category: str, 
                           budget: Optional[float] = None,
                           include_alternatives: bool = True,
                           alternatives_count: int = 5,
                           gender: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Find products matching a given query and category with retry logic.
    
    Args:
        query: Search query for the product
        category: Product category
        budget: Optional budget constraint
        include_alternatives: Whether to include alternative products
        alternatives_count: Number of alternative products to include
        gender: Optional gender filter
        
    Returns:
        List of matching products
    """
    cache_key = f"products:{query}:{category}:{budget}:{gender}"
    cached_products = cache_service.get(cache_key)
    if cached_products:
        logger.info(f"Using cached results for {category} - {query}")
        return cached_products
    
    # Add retry logic
    max_retries = 2
    search_count = alternatives_count + 1 if include_alternatives else 3  # Main product + alternatives
    
    for attempt in range(max_retries):
        try:
            logger.info(f"SerpAPI search attempt {attempt+1}/{max_retries} for {category} - {query}")
            
            # Get service instance
            serpapi_service_instance = get_serpapi_service()
            
            # Primary search with original query
            search_query = query
            if attempt == 1:
                # Try simplified query on second attempt
                words = query.split()
                search_query = f"{category} {words[0]}" if words else category
                logger.info(f"Using simplified query: {search_query}")
            
            products = await serpapi_service_instance.search_products(
                query=search_query,
                category=category,
                num_products=search_count,
                gender=gender
            )
            
            if products:
                logger.info(f"Found {len(products)} products for {category}")
                cache_service.set(cache_key, products)
                return products
                
            # Wait between attempts
            if attempt < max_retries - 1:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error in product search attempt {attempt+1}: {str(e)}")
            # Wait between attempts
            if attempt < max_retries - 1:
                await asyncio.sleep(1)
    
    # After all retries, check if we can use similar products from cache
    similar_products = _get_similar_cached_products(query, category)
    if similar_products:
        logger.info(f"Using similar products from cache for {category} - {query}")
        return similar_products
    
    # Final fallback
    logger.warning(f"All attempts failed, using fallback products for {category} - {query}")
    return _get_fallback_items(items)

def _get_similar_cached_products(query: str, category: Optional[str]) -> List[Dict[str, Any]]:
    """
    Find similar products in cache based on keywords.
    """
    if not category:
        return []
    
    # Get all product cache keys
    all_keys = list(cache_service._get_cache_by_level("medium").keys())
    product_keys = [k for k in all_keys if k.startswith("products:")]
    
    # Filter by category first
    category_keys = [k for k in product_keys if f":{category}:" in k]
    if not category_keys:
        category_keys = product_keys  # Fallback to all product keys
    
    # Find best match based on query keywords
    query_words = set(query.lower().split())
    best_key = None
    best_match_count = 0
    
    for key in category_keys:
        key_words = set(key.lower().split(":")[1].split())
        match_count = len(query_words.intersection(key_words))
        
        if match_count > best_match_count:
            best_match_count = match_count
            best_key = key
    
    # Require at least one word match
    if best_match_count > 0 and best_key:
        products = cache_service.get(best_key)
        if products:
            return products
    
    return []

async def enhance_outfits_with_products(outfit_concepts: List[Dict[str, Any]], 
                              request: OutfitGenerateRequest) -> List[Outfit]:
    """
    Match real products to outfit concepts using parallel processing.
    
    Args:
        outfit_concepts: Concepts generated by Claude
        request: Original user request
        
    Returns:
        List of Outfit objects with products matched where possible
    """
    enhanced_outfits = []
    logger.info(f"Processing {len(outfit_concepts)} outfit concepts")
    
    for idx, concept in enumerate(outfit_concepts):
        try:
            # Create a unique ID for the outfit
            outfit_id = str(uuid.uuid4())
            
            # Extract basic outfit information
            outfit_name = concept.get("outfit_name", "Stylish Outfit")
            outfit_description = concept.get("description", "A stylish outfit recommendation")
            outfit_style = concept.get("style", _determine_style(outfit_name, outfit_description, request.prompt))
            outfit_occasion = concept.get("occasion", "Casual")
            items_data = concept.get("items", [])
            
            # Process all items in parallel for speed
            outfit_items = []
            total_price = 0.0
            brands = {}
            
            # Use asyncio.gather to process items in parallel
            if items_data:
                # Prepare all item search tasks
                item_tasks = []
                for item_idx, item_concept in enumerate(items_data):
                    # Get standardized category
                    item_category = _match_categories(item_concept.get("category", ""))
                    
                    # Build search query from item data
                    description = item_concept.get("description", "")
                    color = item_concept.get("color", "")
                    keywords = item_concept.get("search_keywords", [])
                    
                    # Combine all item data into a search query
                    search_parts = []
                    if color and color.lower() not in description.lower():
                        search_parts.append(color)
                    search_parts.append(description)
                    if keywords:
                        search_parts.extend(keywords[:2])  # Only use first 2 keywords to avoid over-specific queries
                    
                    search_query = " ".join(search_parts)
                    
                    # Create task for this item
                    task = _find_products_for_item(
                        query=search_query,
                        category=item_category, 
                        budget=request.budget,
                        include_alternatives=request.include_alternatives,
                        gender=request.gender
                    )
                    item_tasks.append((item_concept, item_category, task))
                
                # Process tasks in batches of 3 to avoid overloading the API
                batch_size = 3
                for i in range(0, len(item_tasks), batch_size):
                    batch = item_tasks[i:i+batch_size]
                    
                    # Wait for batch to complete
                    batch_results = []
                    for item_concept, category, task in batch:
                        try:
                            products = await task
                            batch_results.append((item_concept, category, products))
                        except Exception as e:
                            logger.error(f"Error processing item: {str(e)}")
                            batch_results.append((item_concept, category, []))
                    
                    # Process batch results
                    for item_concept, category, products in batch_results:
                        if products:
                            # First product is the main match
                            main_product = products[0]
                            alternatives = products[1:] if len(products) > 1 else []
                            
                            # Track brand for brand display
                            brand = main_product.get("brand", "")
                            if brand:
                                brands[brand] = brands.get(brand, 0) + 1
                            
                            # Get price
                            price = float(main_product.get("price", 0.0))
                            total_price += price
                            
                            # Create the outfit item
                            outfit_item = OutfitItem(
                                product_id=main_product.get("product_id", str(uuid.uuid4())),
                                product_name=main_product.get("product_name", item_concept.get("description", "")),
                                brand=brand,
                                category=category,
                                price=price,
                                url=main_product.get("url", ""),
                                image_url=main_product.get("image_url", ""),
                                description=main_product.get("description", ""),
                                concept_description=item_concept.get("description", ""),
                                color=item_concept.get("color", ""),
                                alternatives=alternatives,
                                is_fallback=False
                            )
                        else:
                            # Create fallback item if no products found
                            logger.warning(f"No products found for {category}, using fallback")
                            mock_product = _get_mock_product(category, item_concept.get("description"), item_concept.get("color"))
                            
                            outfit_item = OutfitItem(
                                product_id=f"fallback-{uuid.uuid4()}",
                                product_name=mock_product.get("name", item_concept.get("description", "")),
                                brand=mock_product.get("brand", "Various"),
                                category=category,
                                price=29.99,  # Default fallback price
                                url="",
                                image_url=mock_product.get("image_url", ""),
                                description=item_concept.get("description", ""),
                                concept_description=item_concept.get("description", ""),
                                color=item_concept.get("color", ""),
                                alternatives=[],
                                is_fallback=True
                            )
                            total_price += 29.99
                        
                        outfit_items.append(outfit_item)
            
            # Create brand display info
            brand_display = {}
            if brands:
                # Sort brands by frequency
                sorted_brands = sorted(brands.items(), key=lambda x: x[1], reverse=True)
                # Keep top 3 brands
                for brand, count in sorted_brands[:3]:
                    brand_display[brand] = str(count)
            
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
                    _add_collage_to_outfit(outfit)
                except Exception as collage_error:
                    logger.error(f"Error creating collage: {str(collage_error)}")
            
            enhanced_outfits.append(outfit)
            
        except Exception as outfit_error:
            logger.error(f"Error enhancing outfit concept: {str(outfit_error)}")
            # Continue with next outfit instead of failing completely
            
    # Check if we have any enhanced outfits
    if not enhanced_outfits:
        logger.warning("No outfits could be enhanced, using mockups")
        # Convert mock outfits to Outfit objects
        mock_outfits = []
        for mock in get_mock_outfits():
            if isinstance(mock, dict):
                mock_outfits.append(Outfit(**mock))
            else:
                mock_outfits.append(mock)
        return mock_outfits
        
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
                                alternatives_count=8,  # Get more alternatives when explicitly requested
                                gender=item.get("gender")
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
                _add_collage_to_outfit(outfit_obj)
                
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

# Remove Depends from debug endpoint as well for consistency in testing
@router.get("/debug/check-serpapi", response_model=Dict[str, Any])
async def debug_check_serpapi(): 
    """
    Debug endpoint to test if SerpAPI key is valid and working.
    """
    logger.info("Checking SerpAPI key validity")
    
    # Get service instance directly
    serpapi_service_instance = get_serpapi_service()

    # Test if the SerpAPI key is valid using the direct instance
    is_valid = await serpapi_service_instance.test_api_key()
    
    return {
        "status": "ok" if is_valid else "error",
        "message": "SerpAPI key is valid" if is_valid else "SerpAPI key is invalid or not configured",
        "api_key_configured": serpapi_service_instance.api_key is not None,
        "timestamp": datetime.now().isoformat()
    } 

# Test SerpAPI endpoint with SSL fixes
@router.get("/test-serpapi-ssl", include_in_schema=False)
async def test_serpapi_ssl():
    """Test endpoint to verify SerpAPI works with SSL fix"""
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info("Testing SerpAPI with SSL fix")
    
    try:
        # Get SerpAPI service instance
        serpapi_service_instance = get_serpapi_service()
        
        # Test if key is valid
        is_valid = await serpapi_service_instance.test_api_key()
        
        if is_valid:
            # Try a simple product search
            products = await serpapi_service_instance.search_products(
                query="blue jeans",
                category="Bottom",
                num_products=1
            )
            
            if products:
                first_product = products[0]
                is_fallback = "fallback" in first_product.get("product_id", "")
                
                return {
                    "status": "success",
                    "key_valid": True,
                    "got_products": True,
                    "product_count": len(products),
                    "is_fallback": is_fallback,
                    "first_product": {
                        k: v for k, v in first_product.items() 
                        if k != "image_url"  # Exclude image URL to keep response small
                    }
                }
            else:
                return {
                    "status": "partial_success",
                    "key_valid": True,
                    "got_products": False,
                    "error": "No products returned"
                }
        else:
            return {
                "status": "error",
                "key_valid": False,
                "error": "SerpAPI key is invalid"
            }
    except Exception as e:
        logger.error(f"Error testing SerpAPI: {str(e)}")
        return {
            "status": "error",
            "message": f"Error testing SerpAPI: {str(e)}"
        } 

async def match_products_to_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Match outfit items to real products using search API.
    
    Args:
        items: List of outfit item descriptions
        
    Returns:
        Enhanced items with matched product details
    """
    enhanced_items = []
    
    # Don't proceed without API key
    api_key = os.environ.get("SERPAPI_API_KEY")
    logger.info(f"SERPAPI_API_KEY status: {'Found' if api_key else 'Missing'}")
    if not api_key:
        logger.error("Missing SERPAPI_API_KEY environment variable")
        return create_fallback_items(items)
    
    # Get search optimizer instance
    search_optimizer = get_search_optimizer()
    logger.info("Using search optimizer for product matching")
    
    # Use gather to process items concurrently with a limit
    # Process in batches of 3 to avoid overwhelming the API
    batch_size = 3
    for i in range(0, len(items), batch_size):
        batch = items[i:i+batch_size]
        batch_results = await asyncio.gather(
            *[process_single_item(item, search_optimizer) for item in batch],
            return_exceptions=True
        )
        
        for result in batch_results:
            if isinstance(result, Exception):
                logger.error(f"Batch processing error: {str(result)}")
                # Add fallback item as placeholder
                enhanced_items.append(create_fallback_item({}))
            else:
                enhanced_items.append(result)
    
    return enhanced_items


async def process_single_item(item: Dict[str, Any], search_optimizer=None) -> Dict[str, Any]:
    """Process a single outfit item to find a matching product."""
    try:
        # Skip if missing required fields
        if not item.get('category') or not item.get('description'):
            logger.warning(f"Skipping item with missing fields: {item}")
            return create_fallback_item(item)
        
        # Use search optimizer if provided
        if search_optimizer:
            # Enhance item with additional search terms
            enhanced_item = search_optimizer.enhance_item_for_search(item)
            
            # Get optimized primary query and fallbacks
            primary_query, fallback_queries = search_optimizer.optimize_search_query(enhanced_item)
            
            logger.info(f"Optimized query: {primary_query}")
            if fallback_queries:
                logger.debug(f"Fallback queries: {fallback_queries[:2]}...")
                
            # Try primary query first
            matched_product = await search_product_with_retry(primary_query)
            
            # If primary query fails, try fallbacks in sequence
            if not matched_product and fallback_queries:
                for i, fallback_query in enumerate(fallback_queries[:3]):  # Try up to 3 fallbacks
                    logger.info(f"Trying fallback query {i+1}: {fallback_query}")
                    matched_product = await search_product_with_retry(fallback_query)
                    if matched_product:
                        logger.info(f"Fallback query {i+1} succeeded")
                        break
        else:
            # Fall back to original logic if optimizer not available
            query = build_search_query(item)
            
            if not query.strip():
                logger.warning(f"Empty search query for item: {item}")
                return create_fallback_item(item)
                
            logger.info(f"Searching for product: {query}")
            matched_product = await search_product_with_retry(query)
        
        if matched_product:
            # Successfully found a product
            enhanced_item = {**item, **matched_product}
            logger.info(f"Found product match: {matched_product.get('title', 'No title')} - ${matched_product.get('price', 'N/A')}")
            return enhanced_item
        else:
            # No product found, create fallback
            logger.warning(f"No product match found for item")
            return create_fallback_item(item)
            
    except Exception as e:
        logger.error(f"Error matching product for item: {str(e)}", exc_info=True)
        return create_fallback_item(item)


def build_search_query(item: Dict[str, Any]) -> str:
    """Build an optimized search query from item details."""
    search_terms = item.get('search_keywords', [])
    color = item.get('color', '')
    category = item.get('category', '')
    brand = item.get('brand', '')
    
    # Use search keywords if available, otherwise build from description
    if search_terms and len(search_terms) > 0:
        # Filter out empty strings and join with spaces
        query_terms = [term for term in search_terms if term and len(term.strip()) > 0]
        
        # Add important attributes not present in search terms
        if color and color.lower() not in ' '.join(query_terms).lower():
            query_terms.append(color)
        if category and category.lower() not in ' '.join(query_terms).lower():
            query_terms.append(category)
        if brand and brand.lower() not in ' '.join(query_terms).lower() and len(brand) < 20:
            query_terms.insert(0, brand)  # Put brand first for better results
    else:
        # Fall back to description-based query with smart filtering
        description = item.get('description', '')
        # Clean description - remove filler words for better search
        description = re.sub(r'\b(a|an|the|with|for|and|or|that|this|these|those)\b', ' ', description, flags=re.IGNORECASE)
        description = re.sub(r'\s+', ' ', description).strip()
        
        query_terms = []
        if brand and len(brand) < 20:
            query_terms.append(brand)
        if color:
            query_terms.append(color)
        if category:
            query_terms.append(category)
        if description:
            # Use first 5 words of description for more focused search
            desc_words = description.split()[:5]
            query_terms.append(' '.join(desc_words))
            
    # Join and truncate long queries
    query = ' '.join([term for term in query_terms if term and len(term.strip()) > 0])
    query = query[:100] if len(query) > 100 else query
    
    return query


async def search_product_with_retry(query: str) -> Optional[Dict[str, Any]]:
    """
    Search for a product with retry logic.
    
    Args:
        query: The search query string
        
    Returns:
        Matched product information or None if not found
    """
    max_attempts = 3
    backoff_factor = 2
    initial_backoff = 1  # Start with 1 second backoff
    
    # Create SSL context
    try:
        import ssl
        import certifi
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        logger.debug("Created SSL context with certifi certificates")
    except Exception as e:
        logger.warning(f"Could not create SSL context with certifi: {e}")
        # Fallback to less secure but functional SSL context
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        logger.warning("SSL certificate verification disabled for SerpAPI requests")
    
    for attempt in range(max_attempts):
        current_backoff = initial_backoff * (backoff_factor ** attempt)
        
        try:
            # Build search parameters with clothing-specific filtering
            search_params = {
                "q": query + " clothing",
                "tbm": "shop",
                "num": 5,
                "api_key": os.environ.get("SERPAPI_API_KEY"),
                "tbs": "mr:1",  # Show highly rated items first
            }
            
            # Make search request with timeout
            timeout = aiohttp.ClientTimeout(total=15)  # 15 seconds total timeout
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            
            async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
                async with session.get(
                    "https://serpapi.com/search.json", 
                    params=search_params
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.warning(f"SerpAPI returned status {response.status} (attempt {attempt+1}): {error_text[:200]}")
                        if attempt < max_attempts - 1:
                            logger.info(f"Retrying in {current_backoff} seconds...")
                            await asyncio.sleep(current_backoff)
                        continue
                        
                    try:
                        data = await response.json()
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse JSON response: {str(e)}")
                        if attempt < max_attempts - 1:
                            await asyncio.sleep(current_backoff)
                        continue
                    
                    if not data:
                        logger.warning("Empty response data")
                        if attempt < max_attempts - 1:
                            await asyncio.sleep(current_backoff)
                        continue
                        
                    if "error" in data:
                        logger.error(f"API error: {data['error']}")
                        if attempt < max_attempts - 1:
                            await asyncio.sleep(current_backoff)
                        continue
                    
                    if "shopping_results" not in data or not data["shopping_results"]:
                        logger.warning(f"No shopping results found (attempt {attempt+1})")
                        if attempt < max_attempts - 1:
                            await asyncio.sleep(current_backoff)
                        continue
                    
                    # Find best matching product from results
                    shopping_results = data["shopping_results"]
                    selected_product = select_best_product(shopping_results, query)
                    
                    if not selected_product:
                        logger.warning("No suitable product found in results")
                        if attempt < max_attempts - 1:
                            await asyncio.sleep(current_backoff)
                        continue
                    
                    # Extract and normalize product data
                    return {
                        "product_id": str(uuid.uuid4()),
                        "title": selected_product.get("title", ""),
                        "brand": extract_brand(selected_product),
                        "source": selected_product.get("source", ""),
                        "price": extract_price(selected_product.get("price", "")),
                        "image_url": selected_product.get("thumbnail", ""),
                        "product_url": selected_product.get("link", ""),
                        "delivery": selected_product.get("delivery", ""),
                        "rating": selected_product.get("rating", 0),
                        "reviews": selected_product.get("reviews", 0),
                    }
                    
        except aiohttp.ClientError as e:
            logger.error(f"API request error (attempt {attempt+1}): {str(e)}")
        except asyncio.TimeoutError:
            logger.error(f"API request timeout after 15 seconds (attempt {attempt+1})")
        except Exception as e:
            logger.error(f"Unexpected error during product search (attempt {attempt+1}): {str(e)}", exc_info=True)
        
        # If we got here, the attempt failed
        if attempt < max_attempts - 1:
            logger.info(f"Retrying product search in {current_backoff} seconds...")
            await asyncio.sleep(current_backoff)
    
    # All attempts failed
    logger.error(f"All {max_attempts} attempts to search for product failed: {query}")
    return None


def select_best_product(products: List[Dict[str, Any]], query: str) -> Optional[Dict[str, Any]]:
    """Select the best matching product from results based on relevance."""
    if not products:
        return None
        
    # Simple scoring system for product relevance
    query_terms = set(query.lower().split())
    
    scored_products = []
    for product in products:
        title = product.get("title", "").lower()
        
        # Calculate term match score
        term_match_score = sum(1 for term in query_terms if term in title)
        
        # Prioritize products with images
        has_image = 1 if product.get("thumbnail") else 0
        
        # Prioritize products with ratings
        has_rating = 1 if product.get("rating") else 0
        
        # Calculate final score
        score = term_match_score + has_image*2 + has_rating
        
        scored_products.append((score, product))
    
    # Sort by score (highest first)
    scored_products.sort(reverse=True, key=lambda x: x[0])
    
    # Return highest scoring product
    return scored_products[0][1] if scored_products else None


def extract_brand(product: Dict[str, Any]) -> str:
    """Extract brand information from product data."""
    # If brand is explicitly provided
    if "brand" in product and product["brand"]:
        return product["brand"]
    
    # Try to extract from source
    source = product.get("source", "")
    if source and not source.lower().startswith("http"):
        return source.split()[0]  # Often the first word is the brand
    
    # Try to extract from title
    title = product.get("title", "")
    if title:
        # Common brand positioning is at the start of title
        title_parts = title.split()
        if len(title_parts) > 0:
            potential_brand = title_parts[0]
            # Most brands are capitalized and not extremely long
            if potential_brand[0].isupper() and len(potential_brand) < 15:
                return potential_brand
    
    return "Fashion Brand"


def extract_price(price_str: str) -> float:
    """Extract numerical price from string format."""
    if not price_str:
        return 29.99  # Default price
    
    try:
        # Remove currency symbols and commas
        clean_price = re.sub(r'[^\d.]', '', price_str)
        
        # Handle empty string after cleaning
        if not clean_price:
            return 29.99
        
        price = float(clean_price)
        # Sanity check on price range
        if price < 0.1 or price > 10000:
            return 29.99
        return price
    except (ValueError, TypeError):
        return 29.99  # Default price on error


def create_fallback_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """Create a fallback item when product matching fails."""
    category = item.get('category', 'Item')
    color = item.get('color', 'Stylish')
    
    fallback = {
        "product_id": str(uuid.uuid4()),
        "title": f"{color} {category}",
        "brand": "Fashion Brand",
        "source": "Fashion Store",
        "price": 29.99,
        "image_url": get_default_image_for_category(category),
        "product_url": "https://example.com/product",
        "delivery": "Standard delivery",
        "rating": 4.5,
        "reviews": 42,
    }
    
    # Preserve original item fields
    return {**item, **fallback}


def create_fallback_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Create fallback items for an entire list"""
    return [create_fallback_item(item) for item in items]


def get_default_image_for_category(category: str) -> str:
    """Get a default image URL based on item category."""
    category = category.lower() if category else ""
    
    # Define category to image mapping
    category_images = {
        "shirt": "https://example.com/images/shirt.jpg",
        "t-shirt": "https://example.com/images/tshirt.jpg",
        "jeans": "https://example.com/images/jeans.jpg",
        "pants": "https://example.com/images/pants.jpg",
        "dress": "https://example.com/images/dress.jpg",
        "shoes": "https://example.com/images/shoes.jpg",
        "sneakers": "https://example.com/images/sneakers.jpg",
        "jacket": "https://example.com/images/jacket.jpg",
        "coat": "https://example.com/images/coat.jpg",
        "sweater": "https://example.com/images/sweater.jpg",
        "hat": "https://example.com/images/hat.jpg",
        "bag": "https://example.com/images/bag.jpg",
        "handbag": "https://example.com/images/handbag.jpg",
        "scarf": "https://example.com/images/scarf.jpg",
        "sunglasses": "https://example.com/images/sunglasses.jpg",
        "watch": "https://example.com/images/watch.jpg",
        "necklace": "https://example.com/images/necklace.jpg",
        "earrings": "https://example.com/images/earrings.jpg",
        "bracelet": "https://example.com/images/bracelet.jpg",
        "ring": "https://example.com/images/ring.jpg",
    }
    
    # Check if we have a matching category image
    for key, url in category_images.items():
        if key in category:
            return url
    
    # Default image if no match
    return "https://example.com/images/clothing.jpg" 

@router.post("/run-serpapi-analysis", include_in_schema=False)
async def run_serpapi_analysis(iterations: int = 10):
    """
    Admin endpoint to run SerpAPI analysis
    This will make multiple API calls to analyze search patterns
    """
    # Prevent abuse by requiring authentication in production
    if not settings.debug:
        return {"error": "This endpoint is only available in debug mode"}
        
    try:
        # Import analyzer dynamically
        from app.services.serpapi_analyzer import SerpAPIAnalyzer
        
        # Run in background task to not block response
        background_tasks = BackgroundTasks()
        
        async def run_analysis():
            try:
                logger.info(f"Starting SerpAPI analysis with {iterations} iterations")
                analyzer = SerpAPIAnalyzer()
                await analyzer.run_analysis(iterations=iterations)
                logger.info("SerpAPI analysis completed")
            except Exception as e:
                logger.error(f"Error in SerpAPI analysis: {e}", exc_info=True)
        
        background_tasks.add_task(run_analysis)
        
        return {
            "message": f"Started SerpAPI analysis with {iterations} iterations in background",
            "success": True
        }
    except ImportError:
        return {"error": "SerpAPI analyzer module not found"}
    except Exception as e:
        logger.error(f"Error starting SerpAPI analysis: {e}")
        return {"error": str(e)}


@router.get("/search-optimization-status")
async def search_optimization_status():
    """Get the current search optimization status and recommendations"""
    try:
        search_optimizer = get_search_optimizer()
        recommendations = search_optimizer.get_search_recommendations()
        
        return {
            "analysis_loaded": search_optimizer.analysis_loaded,
            "recommendations": recommendations,
            "success": True
        }
    except Exception as e:
        logger.error(f"Error getting search optimization status: {e}")
        return {"error": str(e)} 