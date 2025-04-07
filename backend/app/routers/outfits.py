from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import json
import random

router = APIRouter(
    prefix="/outfits",
    tags=["outfits"],
    responses={404: {"description": "Not found"}},
)

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

# Routes
@router.post("/generate", response_model=OutfitGenerateResponse)
async def generate_outfit(request: OutfitGenerateRequest):
    """Generate outfit recommendations based on user preferences"""
    try:
        from app.routers.products import get_real_products
        
        # Get real products for outfit generation
        real_products = []
        
        # Get different types of products for a complete outfit
        categories = ["tops", "bottoms", "shoes", "accessories", "outerwear", "dresses"]
        
        for category in categories:
            # Get products for each category
            category_products = await get_real_products(
                category=category, 
                page=1, 
                page_size=10  # Increased to get more product variety
            )
            
            if category_products:
                real_products.extend(category_products)
        
        # If no real products were found, fall back to mock data
        if not real_products:
            outfits = get_mock_outfits()
        else:
            # Determine budget tier based on user input
            budget_tier = "any"
            if request.budget:
                if request.budget >= 1000:
                    budget_tier = "luxury"
                elif request.budget >= 400:
                    budget_tier = "premium"
                elif request.budget >= 150:
                    budget_tier = "mid-range"
                else:
                    budget_tier = "budget"
            
            # Group products by category
            products_by_category = {}
            for product in real_products:
                category = product.get("category", "").lower()
                if category not in products_by_category:
                    products_by_category[category] = []
                products_by_category[category].append(product)
            
            # Pre-filter products by price for budget constraint
            if request.budget:
                # Get max price per category based on budget distribution
                # Typical budget distribution: tops 20%, bottoms 25%, shoes 25%, accessories 15%, outerwear 15%
                max_top_price = request.budget * 0.2
                max_bottom_price = request.budget * 0.25
                max_shoe_price = request.budget * 0.25
                max_accessory_price = request.budget * 0.15
                max_outerwear_price = request.budget * 0.15
                max_dress_price = request.budget * 0.45  # If using a dress instead of top+bottom
                
                # Filter each category by its max price
                if "tops" in products_by_category:
                    products_by_category["tops"] = [p for p in products_by_category["tops"] if p["price"] <= max_top_price]
                if "bottoms" in products_by_category:
                    products_by_category["bottoms"] = [p for p in products_by_category["bottoms"] if p["price"] <= max_bottom_price]
                if "shoes" in products_by_category:
                    products_by_category["shoes"] = [p for p in products_by_category["shoes"] if p["price"] <= max_shoe_price]
                if "accessories" in products_by_category:
                    products_by_category["accessories"] = [p for p in products_by_category["accessories"] if p["price"] <= max_accessory_price]
                if "outerwear" in products_by_category:
                    products_by_category["outerwear"] = [p for p in products_by_category["outerwear"] if p["price"] <= max_outerwear_price]
                if "dresses" in products_by_category:
                    products_by_category["dresses"] = [p for p in products_by_category["dresses"] if p["price"] <= max_dress_price]
            
            # Create outfits from real products
            outfits = []
            
            # Parse the request prompt to identify style keywords
            prompt_keywords = request.prompt.lower().split()
            is_festival = any(keyword in prompt_keywords for keyword in ["festival", "coachella", "bohemian", "boho"])
            is_casual = any(keyword in prompt_keywords for keyword in ["casual", "everyday", "basic"])
            is_formal = any(keyword in prompt_keywords for keyword in ["formal", "business", "elegant", "office"])
            
            # Budget-aware brand selection
            def get_brand_tier(product_price, category):
                # Adjust thresholds based on category (shoes tend to be more expensive than tops)
                if category == "shoes":
                    if product_price >= 300: return "luxury"
                    elif product_price >= 150: return "premium"
                    elif product_price >= 80: return "mid-range"
                    else: return "budget"
                elif category == "outerwear":
                    if product_price >= 400: return "luxury"
                    elif product_price >= 200: return "premium"
                    elif product_price >= 100: return "mid-range"
                    else: return "budget"
                else:
                    if product_price >= 200: return "luxury"
                    elif product_price >= 100: return "premium"
                    elif product_price >= 50: return "mid-range"
                    else: return "budget"
            
            # Create 3 outfits with different style/brand combinations
            for outfit_index in range(3):
                # Determine outfit style based on index and prompt
                if outfit_index == 0:
                    # First outfit directly based on prompt
                    outfit_style = "festival" if is_festival else "casual" if is_casual else "formal" if is_formal else "trendy"
                elif outfit_index == 1:
                    # Second outfit slightly different style variation
                    if is_festival: outfit_style = "bohemian"
                    elif is_casual: outfit_style = "streetwear"
                    elif is_formal: outfit_style = "business casual"
                    else: outfit_style = "contemporary"
                else:
                    # Third outfit another variation
                    if is_festival: outfit_style = "music festival"
                    elif is_casual: outfit_style = "athleisure"
                    elif is_formal: outfit_style = "smart casual"
                    else: outfit_style = "minimalist"
                
                outfit_name = f"{outfit_style.title()} Look"
                outfit_description = f"AI-generated {outfit_style} outfit based on your preferences"
                
                # Select products for the outfit from appropriate brand tiers
                outfit_items = []
                outfit_total = 0
                desired_tier = budget_tier
                
                # Try to maintain brand coherence by starting with a selected tier
                if "tops" in products_by_category and products_by_category["tops"]:
                    # Filter tops based on budget tier if specified
                    suitable_tops = products_by_category["tops"]
                    if budget_tier != "any":
                        tier_tops = [p for p in suitable_tops if get_brand_tier(p["price"], "tops") == budget_tier]
                        if tier_tops:
                            suitable_tops = tier_tops
                    
                    # Select a top
                    if suitable_tops:
                        top = random.choice(suitable_tops)
                        outfit_items.append(top)
                        outfit_total += top["price"]
                        
                        # Use the selected top's brand tier to guide other selections for coherence
                        if budget_tier == "any":
                            desired_tier = get_brand_tier(top["price"], "tops")
                
                # Add bottoms (unless we're doing a dress outfit)
                dress_outfit = False
                if is_festival and "dresses" in products_by_category and products_by_category["dresses"] and random.random() > 0.5:
                    dress_outfit = True
                    
                    # Filter dresses based on budget tier
                    suitable_dresses = products_by_category["dresses"]
                    if desired_tier != "any":
                        tier_dresses = [p for p in suitable_dresses if get_brand_tier(p["price"], "dresses") == desired_tier]
                        if tier_dresses:
                            suitable_dresses = tier_dresses
                    
                    if suitable_dresses:
                        dress = random.choice(suitable_dresses)
                        outfit_items.append(dress)
                        outfit_total += dress["price"]
                elif not dress_outfit and "bottoms" in products_by_category and products_by_category["bottoms"]:
                    # Filter bottoms based on budget tier
                    suitable_bottoms = products_by_category["bottoms"]
                    if desired_tier != "any":
                        tier_bottoms = [p for p in suitable_bottoms if get_brand_tier(p["price"], "bottoms") == desired_tier]
                        if tier_bottoms:
                            suitable_bottoms = tier_bottoms
                    
                    if suitable_bottoms:
                        bottom = random.choice(suitable_bottoms)
                        outfit_items.append(bottom)
                        outfit_total += bottom["price"]
                
                # Add shoes
                if "shoes" in products_by_category and products_by_category["shoes"]:
                    # Check remaining budget if specified
                    remaining_budget = None
                    if request.budget:
                        remaining_budget = request.budget - outfit_total
                    
                    # Filter shoes based on budget tier
                    suitable_shoes = products_by_category["shoes"]
                    if desired_tier != "any":
                        tier_shoes = [p for p in suitable_shoes if get_brand_tier(p["price"], "shoes") == desired_tier]
                        if tier_shoes:
                            suitable_shoes = tier_shoes
                    
                    # Further filter by remaining budget if applicable
                    if remaining_budget is not None:
                        budget_shoes = [p for p in suitable_shoes if p["price"] <= remaining_budget]
                        if budget_shoes:
                            suitable_shoes = budget_shoes
                    
                    if suitable_shoes:
                        shoes = random.choice(suitable_shoes)
                        outfit_items.append(shoes)
                        outfit_total += shoes["price"]
                
                # Add accessories if budget allows
                if request.budget is None or outfit_total < request.budget * 0.85:
                    if "accessories" in products_by_category and products_by_category["accessories"]:
                        # Calculate remaining budget for accessories
                        remaining_budget = None
                        if request.budget:
                            remaining_budget = request.budget - outfit_total
                        
                        # Filter accessories based on budget tier and remaining budget
                        suitable_accessories = products_by_category["accessories"]
                        if desired_tier != "any":
                            tier_accessories = [p for p in suitable_accessories if get_brand_tier(p["price"], "accessories") == desired_tier]
                            if tier_accessories:
                                suitable_accessories = tier_accessories
                        
                        if remaining_budget is not None:
                            budget_accessories = [p for p in suitable_accessories if p["price"] <= remaining_budget]
                            if budget_accessories:
                                suitable_accessories = budget_accessories
                        
                        if suitable_accessories:
                            accessory = random.choice(suitable_accessories)
                            outfit_items.append(accessory)
                            outfit_total += accessory["price"]
                
                # Add outerwear for non-festival outfits if available and budget allows
                if (not is_festival or random.random() > 0.7) and request.budget is None or outfit_total < request.budget * 0.9:
                    if "outerwear" in products_by_category and products_by_category["outerwear"]:
                        # Calculate remaining budget for outerwear
                        remaining_budget = None
                        if request.budget:
                            remaining_budget = request.budget - outfit_total
                        
                        # Filter outerwear based on budget tier and remaining budget
                        suitable_outerwear = products_by_category["outerwear"]
                        if desired_tier != "any":
                            tier_outerwear = [p for p in suitable_outerwear if get_brand_tier(p["price"], "outerwear") == desired_tier]
                            if tier_outerwear:
                                suitable_outerwear = tier_outerwear
                        
                        if remaining_budget is not None:
                            budget_outerwear = [p for p in suitable_outerwear if p["price"] <= remaining_budget]
                            if budget_outerwear:
                                suitable_outerwear = budget_outerwear
                        
                        if suitable_outerwear:
                            outerwear = random.choice(suitable_outerwear)
                            outfit_items.append(outerwear)
                            outfit_total += outerwear["price"]
                
                # Create the outfit
                if outfit_items:
                    # Add tier information to outfit name
                    if desired_tier != "any":
                        if desired_tier == "luxury":
                            outfit_name = f"Luxury {outfit_name}"
                        elif desired_tier == "premium":
                            outfit_name = f"Premium {outfit_name}"
                        elif desired_tier == "mid-range":
                            outfit_name = f"Contemporary {outfit_name}"
                        elif desired_tier == "budget":
                            outfit_name = f"Affordable {outfit_name}"
                    
                    outfit = {
                        "id": f"outfit_{random.randint(1000, 9999)}",
                        "name": outfit_name,
                        "description": outfit_description,
                        "style": outfit_style,
                        "total_price": round(outfit_total, 2),
                        "items": []
                    }
                    
                    # Format items to match OutfitItem model
                    for item in outfit_items:
                        outfit_item = {
                            "product_id": item["id"],
                            "product_name": item["name"],
                            "brand": item["brand"],
                            "category": item["category"],
                            "price": item["price"],
                            "url": item.get("url", ""),
                            "image_url": item["image_url"],
                            "description": item["description"]
                        }
                        outfit["items"].append(outfit_item)
                    
                    outfits.append(outfit)
        
        # Apply filters based on request
        filtered_outfits = outfits
        
        # Filter by budget
        if request.budget:
            filtered_outfits = [o for o in filtered_outfits if o["total_price"] <= request.budget]
        
        # Filter by preferred brands (if any match)
        if request.preferred_brands:
            brand_list = [brand.lower() for brand in request.preferred_brands]
            filtered_outfits = [o for o in filtered_outfits if 
                              any(item["brand"].lower() in brand_list for item in o["items"])]
        
        # Filter by style keywords (if any match)
        if request.style_keywords:
            style_list = [style.lower() for style in request.style_keywords]
            filtered_outfits = [o for o in filtered_outfits if 
                              any(keyword in o["style"].lower() for keyword in style_list) or
                              any(keyword in o["name"].lower() for keyword in style_list) or
                              any(keyword in o["description"].lower() for keyword in style_list)]
        
        # Use mock data if no outfits match the filters
        if not filtered_outfits:
            filtered_outfits = get_mock_outfits()
            
            # Apply budget filter to mock outfits if specified
            if request.budget:
                filtered_outfits = [o for o in filtered_outfits if o["total_price"] <= request.budget]
        
        # Convert to Outfit models
        outfit_models = [Outfit(**o) for o in filtered_outfits]
        
        return OutfitGenerateResponse(
            outfits=outfit_models,
            prompt=request.prompt
        )
        
    except Exception as e:
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