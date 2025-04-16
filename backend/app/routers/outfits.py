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
1.  **Analyze Prompt:** Carefully understand the user's request, identifying key elements like occasion, desired style (e.g., casual, formal, boho, minimalist, streetwear), season, weather (if mentioned), specific item requests, and any constraints (e.g., budget level - budget, mid-range, premium, luxury).
2.  **Consider Context:** Factor in general fashion principles, color theory, item compatibility, layering possibilities (if relevant to season/weather), and current relevant fashion trends (mention specific trends like 'quiet luxury', 'Y2K revival', 'dopamine dressing' if appropriate, but don't force them).
3.  **Generate Outfit Concepts:** Create 2-3 distinct outfit options that fulfill the user's request. Each outfit should be a complete look.
4.  **Itemize:** For each outfit concept, specify the necessary item categories (e.g., top, bottom, dress, outerwear, shoes, bag, accessory).
5.  **Describe Items:** Provide a concise description for each item, including its type and suggested color or material (e.g., "Cream silk blouse", "Dark wash straight-leg jeans", "Black leather ankle boots", "Gold pendant necklace"). Be specific enough to guide product search but generic enough to allow for variations.
6.  **Add Keywords:** For each item, provide a list of relevant keywords that could be used to find similar products online (e.g., ["blouse", "silk", "cream", "long sleeve", "formal"], ["jeans", "denim", "dark wash", "straight leg", "casual"]).
7.  **Provide Rationale:** For each complete outfit, write a short "Stylist Rationale" explaining *why* this outfit works for the user's prompt and how the pieces complement each other.
8.  **Output Format:** Respond *only* in valid JSON format. The structure must be:
    ```json
    {
      "outfits": [
        {
          "outfit_name": "Example Outfit Name 1",
          "items": [
            {
              "category": "Top",
              "description": "Item description (e.g., White cotton t-shirt)",
              "color": "Suggested color (e.g., White)",
              "keywords": ["keyword1", "keyword2", "category"]
            },
            {
              "category": "Bottom",
              "description": "Item description (e.g., Blue denim jeans)",
              "color": "Suggested color (e.g., Blue)",
              "keywords": ["keyword3", "keyword4", "category"]
            }
            // ... other items (shoes, outerwear, accessories etc.)
          ],
          "stylist_rationale": "Explanation why this outfit works..."
        }
        // ... potentially more outfit objects
      ]
    }
    ```

**Constraints & Guidelines:**
*   Always provide the response in the specified JSON format. Do not include any text outside the JSON structure.
*   Ensure outfits are complete and make sense for the request.
*   Suggest standard item categories (Top, Bottom, Dress, Outerwear, Shoes, Bag, Accessory).
*   Item descriptions should be clear but not overly specific to one exact product unless requested.
*   Keywords should be relevant for searching online fashion retailers.
*   If the user prompt is ambiguous or lacks detail, you can make reasonable assumptions based on common fashion sense, but state them briefly in the rationale if necessary. Avoid asking clarifying questions in the JSON output.
*   Maintain a helpful, knowledgeable, and inspiring stylist tone within the 'stylist_rationale'.
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
async def generate_outfit(request: OutfitGenerateRequest = Body(...)):
    """
    Generate an outfit based on user preferences using the Anthropic API.
    Source real products for the outfit items using SerpAPI.
    Create a collage of the outfit items.
    """
    try:
        # Log the request
        logger.info(f"Generating outfit for prompt: {request.prompt}, gender: {request.gender}, budget: {request.budget}")
        
        # Get and prepare prompt
        prompt = request.prompt
        
        # Initialize Anthropic client if api key is available
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        anthropic_client = None
        if anthropic_api_key:
            anthropic_client = anthropic.Anthropic(api_key=anthropic_api_key)

        # --- Use Anthropic API if available ---
        if anthropic_client:
            try:
                print(f"Sending request to Anthropic with prompt: {prompt}")
                message = anthropic_client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=2048,
                    system=SYSTEM_PROMPT,
                    messages=[
                        {
                            "role": "user",
                            "content": f"Generate 2-3 outfit options based on the following request: {prompt}. For gender: {request.gender}. Budget: ${request.budget if request.budget else 'Any'}." + (f"Include {request.include}" if request.include else "")
                        }
                    ]
                )
                
                # --- Process Anthropic Response ---
                print("Received response from Anthropic.")
                response_text = message.content[0].text
                
                # Find the start and end of the JSON block
                json_start = response_text.find('{')
                json_end = response_text.rfind('}')
                
                if json_start != -1 and json_end != -1:
                    json_string = response_text[json_start:json_end+1]
                    try:
                        outfit_data = json.loads(json_string)
                        
                        # --- Process outfits from the response ---
                        if "outfits" in outfit_data and isinstance(outfit_data["outfits"], list):
                            llm_outfits = outfit_data["outfits"]
                            
                            # Process each outfit
                            processed_outfits = []
                            max_budget_per_outfit = request.budget if request.budget else 2000
                            
                            for outfit in llm_outfits:
                                outfit_budget_remaining = max_budget_per_outfit
                                outfit_name = outfit.get("name", "Stylish Outfit")
                                occasion = outfit.get("occasion", "casual")
                                season = outfit.get("season", "any")
                                style = outfit.get("style", "classic")
                                rationale = outfit.get("stylist_rationale", "")
                                
                                # Process each item in the outfit
                                processed_items = []
                                if "items" in outfit and isinstance(outfit["items"], list):
                                    for item in outfit["items"]:
                                        item_category = item.get("category", "").capitalize()
                                        
                                        # Skip if we don't have a valid category
                                        if not item_category:
                                            continue
                                            
                                        # Determine gender-specific search
                                        gender_prefix = ""
                                        if request.gender and request.gender.lower() in ["male", "female"]:
                                            gender_prefix = f"{request.gender} "
                                            
                                        # Create search query
                                        color_desc = item.get("color", "")
                                        description = item.get("description", "")
                                        material = item.get("material", "")
                                        
                                        # Build the search keyword
                                        search_keywords = []
                                        if gender_prefix:
                                            search_keywords.append(gender_prefix)
                                        if color_desc:
                                            search_keywords.append(color_desc)
                                        if material:
                                            search_keywords.append(material)
                                        search_keywords.append(description if description else item_category)
                                        
                                        search_query = " ".join(search_keywords)
                                        
                                        # Maximum price for this item (proportional to total budget)
                                        max_price = min(outfit_budget_remaining, 
                                                      max_budget_per_outfit * (0.5 if item_category in ["Shoes", "Outerwear", "Dress"] else 0.25))
                                        
                                        # If we have SerpAPI service, source real products
                                        real_products = []
                                        if serpapi_service and serpapi_service.api_key:
                                            try:
                                                real_products = serpapi_service.search_products(
                                                    query=search_query,
                                                    category=item_category,
                                                    gender=request.gender,
                                                    max_price=max_price,
                                                    limit=5
                                                )
                                            except Exception as e:
                                                print(f"Error sourcing real products: {str(e)}")
                                                
                                        # Use the top product or create a mock product
                                        if real_products and len(real_products) > 0:
                                            selected_product = real_products[0]
                                            
                                            # Create an outfit item from the real product
                                            item_price = float(selected_product.get("price", 0))
                                            outfit_budget_remaining -= item_price
                                            
                                            # Create the OutfitItem
                                            processed_item = OutfitItem(
                                                product_id=selected_product.get("product_id", str(uuid.uuid4())),
                                                product_name=selected_product.get("title", description),
                                                brand=selected_product.get("source", ""),
                                                category=item_category,
                                                price=item_price,
                                                color=color_desc,
                                                url=selected_product.get("link", ""),
                                                image_url=selected_product.get("thumbnail", ""),
                                                description=description
                                            )
                                            processed_items.append(processed_item)
                                        else:
                                            # Create a mock product if we couldn't find a real one
                                            mock_price = random.uniform(
                                                max_price * 0.3, 
                                                max_price * 0.8
                                            )
                                            outfit_budget_remaining -= mock_price
                                            
                                            # Get mock product details
                                            mock_details = _get_mock_product(item_category, description, color_desc)
                                            
                                            # Create the OutfitItem
                                            processed_item = OutfitItem(
                                                product_id=str(uuid.uuid4()),
                                                product_name=mock_details["name"],
                                                brand=mock_details["brand"],
                                                category=item_category,
                                                price=mock_price,
                                                color=color_desc,
                                                url="",
                                                image_url=mock_details["image_url"],
                                                description=description
                                            )
                                            processed_items.append(processed_item)
                                
                                # Create the processed outfit
                                if processed_items:
                                    # Calculate total price
                                    total_price = sum(item.price for item in processed_items)
                                    
                                    # Create outfit
                                    processed_outfit = Outfit(
                                        outfit_id=str(uuid.uuid4()),
                                        name=outfit_name,
                                        items=processed_items,
                                        occasion=occasion,
                                        season=season,
                                        style=style,
                                        total_price=total_price,
                                        stylist_rationale=rationale
                                    )
                                    
                                    # Create a collage image for the outfit
                                    try:
                                        if len(processed_items) >= 2:
                                            collage, image_map = create_outfit_collage([item.image_url for item in processed_items], 
                                                                                      [item.category for item in processed_items])
                                            processed_outfit.collage_image = collage
                                            processed_outfit.image_map = image_map
                                    except Exception as collage_error:
                                        print(f"Error creating collage: {str(collage_error)}")
                                        
                                    processed_outfits.append(processed_outfit)
                            
                            # Return the processed outfits
                            if processed_outfits:
                                return OutfitGenerateResponse(
                                    outfits=processed_outfits,
                                    prompt=prompt,
                                    status="success",
                                    status_message="Generated outfits successfully"
                                )
                        else:
                            print("Parsed JSON from Anthropic but no valid outfits found.")
                    except json.JSONDecodeError as json_err:
                        print(f"Error decoding JSON from Anthropic: {json_err}")
                        print(f"Received text: {response_text}")
                else:
                    print("Could not find valid JSON block in Anthropic response.")
                    print(f"Received text: {response_text}")
            except Exception as e:
                print(f"Error calling Anthropic API: {str(e)}")
                # Fall through to use mock data if API fails

        # --- Fallback to Mock Data --- 
        print("Falling back to mock outfit data.")
        try:
            # The original mock/manual generation logic is now the fallback
            mock_outfits_data = get_mock_outfits() # Use existing mock function
            
            # Apply budget filter if needed
            if request.budget:
                mock_outfits_data = [o for o in mock_outfits_data if o["total_price"] <= request.budget]
            
            # Convert to Outfit models
            outfit_models = [Outfit(**o) for o in mock_outfits_data]
            
            # Create collages for mock outfits if they don't have them
            for outfit in outfit_models:
                if not outfit.collage_image and len(outfit.items) >= 2:
                    try:
                        collage, image_map = create_outfit_collage([item.image_url for item in outfit.items], 
                                                                  [item.category for item in outfit.items])
                        outfit.collage_image = collage
                        outfit.image_map = image_map
                    except Exception as collage_error:
                        print(f"Error creating collage for mock outfit: {str(collage_error)}")
            
            return OutfitGenerateResponse(
                outfits=outfit_models[:3], # Limit to 3 mock outfits
                prompt=prompt,
                status="limited",
                status_message="Using mock data due to API limitations",
                using_fallbacks=True
            )
            
        except Exception as e:
            print(f"Error generating mock outfits: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to generate outfits: {str(e)}")
            
    except Exception as e:
        # This is the outer exception handler for the entire generate_outfit function
        print(f"Error generating outfit: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate outfit: {str(e)}")

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