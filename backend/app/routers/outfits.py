from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import json
import random
import logging # Added logging

# --- Added Imports ---
import anthropic
from dotenv import load_dotenv
from app.services.image_service import create_outfit_collage # Keep collage function
from app.services.product_finder import find_real_product_nordstrom # Import the new product finder
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

# Models
class OutfitItem(BaseModel):
    product_id: str
    product_name: str
    brand: str
    category: str
    price: float
    url: str
    image_url: str
    description: Optional[str] = None
    
class Outfit(BaseModel):
    id: str
    name: str
    description: str
    style: str
    total_price: float
    items: List[OutfitItem]
    occasion: Optional[str] = "Everyday"
    brand_display: Optional[Dict[str, str]] = None
    collage_image: Optional[str] = None  # Base64 encoded image for outfit collage
    image_map: Optional[List[Dict[str, Any]]] = None  # Clickable areas for the collage
    
class OutfitGenerateRequest(BaseModel):
    prompt: str
    gender: Optional[str] = "unisex"
    budget: Optional[float] = None
    preferred_brands: Optional[List[str]] = None
    preferred_categories: Optional[List[str]] = None
    style_keywords: Optional[List[str]] = None

class OutfitGenerateResponse(BaseModel):
    outfits: List[Outfit]
    prompt: str

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

# Routes
@router.post("/generate", response_model=OutfitGenerateResponse)
async def generate_outfit(request: OutfitGenerateRequest):
    """Generate outfit recommendations based on user preferences using Anthropic API"""
    # --- Use Anthropic API if available ---
    if anthropic_client:
        try:
            print(f"Sending request to Anthropic with prompt: {request.prompt}")
            message = anthropic_client.messages.create(
                model="claude-3-haiku-20240307",  # Or use sonnet/opus if needed
                max_tokens=2048,
                system=SYSTEM_PROMPT, # Use the detailed system prompt defined above
                messages=[
                    {
                        "role": "user",
                        "content": f"Generate 2-3 outfit options based on the following request: {request.prompt}"
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
                    
                    # --- Ground LLM suggestions in real products ---
                    if "outfits" in outfit_data and isinstance(outfit_data["outfits"], list):
                        llm_outfits = outfit_data["outfits"]
                        
                        formatted_outfits = []
                        outfit_index = 0
                        for llm_outfit in llm_outfits:
                            items_list = []
                            total_price = 0
                            occasion_keywords = ["formal", "casual", "work", "business", "party", "everyday", "weekend"]
                            
                            # Default occasion is "everyday" unless specified
                            outfit_occasion = "Weekend"  # Default
                            for keyword in occasion_keywords:
                                if keyword.lower() in llm_outfit.get("outfit_name", "").lower() or keyword.lower() in request.prompt.lower():
                                    outfit_occasion = keyword.title()
                                    break
                            
                            # Special case for festival
                            if "festival" in request.prompt.lower() or "coachella" in request.prompt.lower():
                                outfit_occasion = "Festival"
                            
                            item_categories = {}
                            
                            if "items" in llm_outfit and isinstance(llm_outfit["items"], list):
                                for item in llm_outfit["items"]:
                                    # Define category here (outside any conditionals) to solve the scope issue
                                    category = item.get("category", "Unknown")
                                    
                                    # Create search keywords from item description and keywords
                                    description = item.get("description", "")
                                    
                                    # Handle keywords properly
                                    keywords = item.get("keywords", [])
                                    if isinstance(keywords, str):
                                        try:
                                            # Try to parse as JSON if it looks like a list
                                            if keywords.startswith('[') and keywords.endswith(']'):
                                                keywords = json.loads(keywords)
                                            else:
                                                # Otherwise split by commas or spaces
                                                keywords = [k.strip() for k in keywords.replace(',', ' ').split()]
                                        except:
                                            # Fallback to empty list if parsing fails
                                            keywords = []
                                    
                                    # Ensure keywords is a list
                                    if not isinstance(keywords, list):
                                        keywords = []
                                    
                                    # Safe handling of keyword string
                                    keyword_str = ' '.join(keywords) if keywords else ""
                                    
                                    # Get color with fallback
                                    color = item.get("color", "")
                                    
                                    # Create more targeted search terms based on category
                                    if category == "Top":
                                        search_keywords = f"{description} {keyword_str} {color} top shirt blouse fashion festival"
                                    elif category == "Bottom":
                                        search_keywords = f"{description} {keyword_str} {color} bottom pants shorts skirt fashion festival"
                                    elif category == "Dress":
                                        search_keywords = f"{description} {keyword_str} {color} dress fashion festival"
                                    elif category == "Shoes":
                                        search_keywords = f"{description} {keyword_str} {color} shoes boots sandals fashion festival"
                                    elif category == "Accessories":
                                        search_keywords = f"{description} {keyword_str} {color} accessories jewelry fashion festival"
                                    elif category == "Outerwear":
                                        search_keywords = f"{description} {keyword_str} {color} jacket coat cardigan fashion festival"
                                    else:
                                        search_keywords = f"{description} {keyword_str} {color} fashion festival"
                                    
                                    print(f"Searching for products: {search_keywords} in category {category}")
                                    
                                    # Call the Nordstrom scraper
                                    real_product = find_real_product_nordstrom(item) 
                                    
                                    if real_product:
                                        logger.info(f"Found product on {real_product.get('source', 'Unknown')}: {real_product.get('name')}")
                                        
                                        # Update total price
                                        total_price += real_product.get('price', 0)
                                        
                                        # Get category from real product if available, else keep LLM's category
                                        category = real_product.get('category', item.get("category", "Unknown")) 
                                        
                                        # Create OutfitItem using real data
                                        outfit_item = {
                                            "product_id": f"{real_product.get('source', 'prod')}-{len(items_list)}", # Simple ID
                                            "product_name": real_product.get('name', 'N/A'),
                                            "brand": real_product.get('brand', 'N/A'),
                                            "category": category,
                                            "price": real_product.get('price', 0.0),
                                            "url": real_product.get('product_url', '#'),
                                            "image_url": real_product.get('image_url', ''), # Need placeholder image?
                                            "description": item.get("description", "") # Use LLM description maybe? Or real one?
                                        }
                                        
                                        items_list.append(outfit_item)
                                        
                                        # Group by category for brand display
                                        brand = real_product.get('brand', 'Unknown Brand')
                                        if category not in item_categories:
                                            item_categories[category] = []
                                        if brand not in item_categories[category]: # Avoid duplicate brands per category
                                             item_categories[category].append(brand)
                                    else:
                                        # Product not found by scraper
                                        logger.warning(f"Could not find real product via scraping for: {item.get('description')}")
                                        # Decide action: skip item, use placeholder, fallback? -> Currently skips.
                                    
                            # Create brand display format (e.g. "Tops: Brand1, Brand2")
                            brand_display = {}
                            for category, brands in item_categories.items():
                                # Format as plural if needed
                                category_plural = f"{category}s" if not category.endswith('s') else category
                                brand_display[category_plural] = ", ".join(brands)
                            
                            # Create formatted outfit object
                            outfit_name = llm_outfit.get("outfit_name", f"Outfit {len(formatted_outfits) + 1}")
                            outfit_style = next((s for s in ["casual", "formal", "bohemian", "streetwear", "classic", "trendy"] 
                                               if s in outfit_name.lower() or s in request.prompt.lower()), "trendy")
                            
                            # Only create outfit if there are successfully sourced items
                            if items_list: 
                                formatted_outfit = {
                                    "id": f"outfit-{len(formatted_outfits) + 1}",
                                    "name": outfit_name,
                                    "description": llm_outfit.get("stylist_rationale", "A curated outfit based on your request"),
                                    "style": outfit_style,
                                    "total_price": round(total_price, 2),
                                    "items": items_list, # Use the list populated with real items
                                    "occasion": outfit_occasion,
                                    "brand_display": brand_display
                                }
                                
                                # Generate collage using the sourced item images
                                collage_items = []
                                for item_data in items_list: # Use items_list which now has real data
                                    if item_data["image_url"]:
                                        collage_items.append({
                                            "image_url": item_data["image_url"],
                                            "category": item_data["category"],
                                            "source_url": item_data.get("url", '#') 
                                        })
                                
                                # Create and add collage image if items were found
                                if collage_items:
                                    try:
                                        collage_result = create_outfit_collage(collage_items)
                                        formatted_outfit["collage_image"] = collage_result["image"]
                                        formatted_outfit["image_map"] = collage_result["map"]
                                    except Exception as collage_err:
                                        logger.error(f"Error creating collage: {collage_err}")
                                        formatted_outfit["collage_image"] = None # Handle collage error
                                        formatted_outfit["image_map"] = None
                                
                                formatted_outfits.append(formatted_outfit)
                            else:
                                logger.warning(f"Skipping outfit '{llm_outfit.get('outfit_name')}' as no real products could be sourced.")

                        print(f"Successfully parsed {len(formatted_outfits)} outfits from Anthropic response.")
                        return {"outfits": formatted_outfits, "prompt": request.prompt}
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
        
        return OutfitGenerateResponse(
            outfits=outfit_models[:3], # Limit to 3 mock outfits
            prompt=request.prompt
        )
        
    except Exception as e:
        print(f"Error generating mock outfits: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate outfits: {str(e)}")

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