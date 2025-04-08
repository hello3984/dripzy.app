from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import json
import random

# --- Added Imports ---
import anthropic
from dotenv import load_dotenv
from app.services.product_scraper import ProductScraper  # Import the product scraper
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

# Initialize product scraper
product_scraper = ProductScraper()

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
                        
                        # Convert to Outfit models with real product data
                        formatted_outfits = []
                        for llm_outfit in llm_outfits:
                            # Add dummy data for required fields if LLM didn't provide them perfectly
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
                            
                            # Process each item in the outfit
                            item_categories = {}  # To group items by category for display
                            
                            for item in llm_outfit.get("items", []):
                                # Create search keywords from item description and keywords
                                search_keywords = f"{request.prompt} {item.get('description', '')} {' '.join(item.get('keywords', []))}"
                                category = item.get("category", "Unknown")
                                
                                # Search for real products matching this item
                                print(f"Searching for products matching: {search_keywords}, category: {category}")
                                matching_products = product_scraper.search_products(
                                    keywords=search_keywords,
                                    category=category,
                                    limit=1  # Just get the best match for each item
                                )
                                
                                if matching_products and len(matching_products) > 0:
                                    # Use real product data
                                    product = matching_products[0]
                                    outfit_item = OutfitItem(
                                        product_id=product["product_id"],
                                        product_name=product["product_name"],
                                        brand=product["brand"],
                                        category=category,
                                        price=product["price"],
                                        url=product["url"],
                                        image_url=product["image_url"],
                                        description=item.get("description", "")
                                    )
                                    items_list.append(outfit_item)
                                    total_price += product["price"]
                                    
                                    # Store in category dictionary for display
                                    if category not in item_categories:
                                        item_categories[category] = []
                                    item_categories[category].append(outfit_item)
                                    
                                else:
                                    # Fallback to placeholder data if no real product found
                                    price = random.uniform(20, 200) # Assign random price for now
                                    total_price += price
                                    outfit_item = OutfitItem(
                                        product_id=f"llm_item_{random.randint(1000,9999)}",
                                        product_name=item.get("description", "N/A"),
                                        brand="AI Suggestion",
                                        category=category,
                                        price=round(price, 2),
                                        url="#",
                                        image_url="https://via.placeholder.com/300x400?text=AI+Item", # Placeholder image
                                        description=item.get("description", "")
                                    )
                                    items_list.append(outfit_item)
                                    
                                    # Store in category dictionary for display
                                    if category not in item_categories:
                                        item_categories[category] = []
                                    item_categories[category].append(outfit_item)
                            
                            # Create brand display text
                            brand_display = {}
                            for category, items in item_categories.items():
                                # For each category group, display the brands
                                if items:
                                    brand_list = [f"{item.brand}" for item in items]
                                    # Convert category name to plural form for display
                                    category_display = category
                                    if category.lower() in ["top", "bottom", "shoe", "accessory", "jacket", "pant", "dress"]:
                                        category_display = f"{category}s"
                                    brand_display[category_display] = ", ".join(brand_list)
                                    
                            # Build outfit description with more detailed style information
                            outfit_description = llm_outfit.get("stylist_rationale", "Generated by AI.")
                            if len(outfit_description) < 20 and "items" in llm_outfit:
                                # Generate a description if LLM didn't provide a good one
                                item_names = [item.get("description", "") for item in llm_outfit["items"]]
                                outfit_description = f"A {llm_outfit.get('outfit_name', 'stylish')} look featuring {', '.join(item_names[:-1])} and {item_names[-1] if item_names else ''}."
                            
                            formatted_outfits.append(
                                Outfit(
                                    id=f"llm_outfit_{random.randint(1000,9999)}",
                                    name=llm_outfit.get("outfit_name", "AI Generated Outfit"),
                                    description=outfit_description,
                                    style=llm_outfit.get("style", "AI Suggested"), # LLM might not provide this explicitly
                                    total_price=round(total_price, 2),
                                    items=items_list,
                                    occasion=outfit_occasion,
                                    brand_display=brand_display
                                )
                            )

                        if formatted_outfits:
                             print(f"Successfully parsed {len(formatted_outfits)} outfits from Anthropic response.")
                             return OutfitGenerateResponse(
                                outfits=formatted_outfits,
                                prompt=request.prompt
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