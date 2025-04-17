"""
Service for generating outfits using Anthropic API and sourcing real products.
"""

import json
import logging
import os
import re
import time
import uuid
from typing import List, Dict, Any, Optional

import anthropic
from fastapi import HTTPException
from pydantic import BaseModel

from app.models.outfit_models import (
    OutfitItem, 
    Outfit, 
    OutfitGenerateRequest, 
    OutfitGenerateResponse
)
from app.services.serpapi_service import serpapi_service
from app.services.collage_service import collage_service

# Initialize logging
logger = logging.getLogger(__name__)

class OutfitService:
    """Service for generating fashion outfits with AI and sourcing real products."""
    
    def __init__(self):
        """Initialize the OutfitService with necessary clients and services."""
        # Initialize Anthropic client if API key is present
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.client = None
        if self.anthropic_api_key:
            self.client = anthropic.Anthropic(api_key=self.anthropic_api_key)
            logger.info("Anthropic client initialized")
        else:
            logger.warning("ANTHROPIC_API_KEY not found. Using mock data for outfit generation.")
        
        # System prompt for the AI fashion stylist
        self.system_prompt = """
You are an AI fashion stylist expert in creating outfit recommendations. You analyze user prompts, understand their requirements, and generate outfit recommendations.

Process:
1. Analyze the user's prompt to understand their style preferences, occasion, season, and any specific requirements.
2. Generate an outfit concept that matches their requirements with attention to style cohesion.
3. Output the outfit in the following JSON format:

```json
{
  "outfits": [
    {
      "outfit_name": "Brief descriptive title of the outfit",
      "description": "2-3 sentence description of the outfit and why it works for the given prompt",
      "occasion": "Formal/Casual/Business/Athletic/etc.",
      "items": [
        {
          "category": "Top/Bottom/Shoes/Accessory/etc.",
          "name": "Specific product name",
          "description": "Brief description including color, material, fit, etc.",
          "color": "Primary color",
          "price": approximate_price_as_number
        }
        // Additional items...
      ]
    }
  ]
}
```

Guidelines:
- Be specific with item descriptions (e.g., "Navy blue slim-fit cotton chinos" instead of just "Pants")
- Ensure the outfit items work well together stylistically
- Consider the user's occasion, weather, and style preferences
- Include 3-5 items per outfit (core clothing items, shoes, and 1-2 accessories)
- Ensure the outfit matches any gender or budget constraints mentioned
- Provide realistic price estimates as numbers

You MUST provide your response in valid JSON format as shown above.
"""
        
    async def generate_outfit(self, request: OutfitGenerateRequest) -> OutfitGenerateResponse:
        """
        Generate one or more outfits based on the user's request.
        
        Args:
            request: The outfit generation request containing prompt, gender, budget
            
        Returns:
            OutfitGenerateResponse: The generated outfits with real products
        """
        logger.info(f"Generating outfit for prompt: {request.prompt}, gender: {request.gender}, budget: {request.budget}")
        
        try:
            # Request outfit recommendation from Anthropic if available
            if self.client:
                outfit_data = await self._generate_with_anthropic(request)
            else:
                # Use mock data if Anthropic client is not available
                outfit_data = self._get_mock_outfit_data(request)
            
            # Process outfits and source real products
            outfits = await self._process_outfits(outfit_data, request)
            
            # Create the response
            return OutfitGenerateResponse(
                outfits=outfits,
                prompt=request.prompt
            )
            
        except Exception as e:
            logger.error(f"Error generating outfit: {str(e)}")
            # Return mock outfit in case of error
            mock_outfits = await self._process_outfits(self._get_mock_outfit_data(request), request)
            return OutfitGenerateResponse(
                outfits=mock_outfits,
                prompt=request.prompt
            )
    
    async def _generate_with_anthropic(self, request: OutfitGenerateRequest) -> Dict[str, Any]:
        """Generate outfit using Anthropic API."""
        try:
            # Build user prompt with gender and budget information
            user_prompt = self._build_user_prompt(request)
            
            # Make API call
            logger.info(f"Calling Anthropic API with prompt: {user_prompt}")
            response = self.client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=2000,
                temperature=0.7,
                system=self.system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            # Extract JSON from response
            response_text = response.content[0].text
            outfit_data = self._extract_json(response_text)
            
            if not outfit_data or "outfits" not in outfit_data:
                logger.warning("Invalid response format from Anthropic API, using mock data")
                return self._get_mock_outfit_data(request)
            
            return outfit_data
            
        except Exception as e:
            logger.error(f"Error in Anthropic API call: {str(e)}")
            return self._get_mock_outfit_data(request)
    
    def _build_user_prompt(self, request: OutfitGenerateRequest) -> str:
        """Build a detailed user prompt with gender and budget information."""
        prompt = f"Generate outfit options for: {request.prompt}"
        
        if request.gender and request.gender != "unisex":
            prompt += f"\nGender: {request.gender}"
        
        if request.budget:
            prompt += f"\nBudget: ${request.budget}"
            
        if request.preferred_brands and len(request.preferred_brands) > 0:
            prompt += f"\nPreferred brands: {', '.join(request.preferred_brands)}"
            
        return prompt
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from the API response text."""
        try:
            # Extract JSON from response using regex
            json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                return json.loads(json_str)
                
            # If no JSON block, try to find raw JSON
            json_match = re.search(r'(\{.*\})', text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                return json.loads(json_str)
                
            # If still no match, try to parse the entire response
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to extract JSON from response: {str(e)}")
            return {"outfits": []}
    
    async def _process_outfits(self, outfit_data: Dict[str, Any], request: OutfitGenerateRequest) -> List[Outfit]:
        """Process outfits from AI response and source real products."""
        outfit_list = []
        
        # Extract outfits from the data
        ai_outfits = outfit_data.get("outfits", [])
        
        for idx, ai_outfit in enumerate(ai_outfits):
            try:
                # Generate a unique ID for the outfit
                outfit_id = str(uuid.uuid4())
                
                # Extract basic outfit information
                outfit_name = ai_outfit.get("outfit_name", f"Outfit {idx+1}")
                outfit_description = ai_outfit.get("description", "A stylish outfit based on your request")
                outfit_occasion = ai_outfit.get("occasion", "Casual")
                
                # Determine outfit style
                outfit_style = self._determine_style(outfit_name, outfit_description, request.prompt)
                
                # Process items and source real products
                outfit_items, total_price, brand_display = await self._process_outfit_items(
                    ai_outfit.get("items", []), 
                    request.gender, 
                    request.budget
                )
                
                # Create outfit with sourced items
                outfit = Outfit(
                    id=outfit_id,
                    name=outfit_name,
                    description=outfit_description,
                    style=outfit_style,
                    occasion=outfit_occasion,
                    items=outfit_items,
                    total_price=total_price,
                    brand_display=brand_display
                )
                
                # Generate collage if we have images
                if outfit_items:
                    await self._add_collage_to_outfit(outfit)
                
                outfit_list.append(outfit)
                
            except Exception as e:
                logger.error(f"Error processing outfit {idx}: {str(e)}")
        
        # If no outfits could be processed, use mock outfit as fallback
        if not outfit_list:
            mock_outfit_data = self._get_mock_outfit_data(request)
            return await self._process_outfits(mock_outfit_data, request)
        
        return outfit_list
    
    def _determine_style(self, name: str, description: str, prompt: str) -> str:
        """Determine outfit style from name, description, and prompt."""
        # Common style keywords to check
        style_keywords = {
            "casual": ["casual", "everyday", "relaxed", "comfort", "lounge", "weekend"],
            "formal": ["formal", "elegant", "dressed up", "sophisticated", "gala", "wedding"],
            "business": ["business", "professional", "office", "work", "meeting", "interview"],
            "streetwear": ["street", "urban", "hip", "cool", "trendy", "skate"],
            "bohemian": ["boho", "bohemian", "earthy", "festival", "hippie", "coachella"],
            "athleisure": ["athletic", "sport", "gym", "workout", "fitness", "active"],
            "vintage": ["vintage", "retro", "classic", "old school", "90s", "80s"]
        }
        
        # Combine text for searching
        combined_text = f"{name} {description} {prompt}".lower()
        
        # Find matching styles
        for style, keywords in style_keywords.items():
            if any(keyword in combined_text for keyword in keywords):
                return style.capitalize()
        
        # Default style
        return "Contemporary"
    
    async def _process_outfit_items(self, ai_items: List[Dict[str, Any]], gender: Optional[str], 
                                   budget: Optional[float]) -> tuple[List[OutfitItem], float, Dict[str, str]]:
        """Process outfit items from AI and source real products."""
        outfit_items = []
        total_price = 0
        item_categories = {}
        
        # Budget allocation for different categories
        budget_allocation = {
            "Top": 0.25,
            "Bottom": 0.25,
            "Dress": 0.4,
            "Shoes": 0.3,
            "Outerwear": 0.35,
            "Accessory": 0.15,
            "Other": 0.2
        }
        
        for item in ai_items:
            try:
                # Extract item information
                category = item.get("category", "")
                name = item.get("name", "")
                description = item.get("description", "")
                color = item.get("color", "")
                
                # Standardize category
                std_category = self._standardize_category(category)
                
                # Skip if unknown category
                if not std_category:
                    continue
                
                # Calculate max price for this item if budget provided
                max_price = None
                if budget:
                    allocation = budget_allocation.get(std_category, 0.25)
                    max_price = budget * allocation
                
                # Create search query for the product
                search_query = f"{gender} {color} {name} {description}"
                
                # Search for real products
                products = serpapi_service.search_products(
                    query=search_query,
                    category=std_category,
                    gender=gender,
                    max_price=max_price,
                    limit=1
                )
                
                if products:
                    product = products[0]
                    
                    # Create outfit item from real product
                    product_id = product.get("product_id", str(uuid.uuid4()))
                    product_name = product.get("product_name", name)
                    brand = product.get("brand", "")
                    price = product.get("price", item.get("price", 0))
                    image_url = product.get("image_url", "")
                    url = product.get("url", "")
                    
                    outfit_item = OutfitItem(
                        product_id=product_id,
                        name=product_name,
                        product_name=product_name,
                        category=std_category,
                        description=description,
                        color=color,
                        price=price,
                        brand=brand,
                        image_url=image_url,
                        url=url
                    )
                    
                    outfit_items.append(outfit_item)
                    total_price += price
                    
                    # Track categories and brands for display
                    if std_category not in item_categories:
                        item_categories[std_category] = []
                    if brand and brand not in item_categories[std_category]:
                        item_categories[std_category].append(brand)
                else:
                    # If no real product found, use the AI-suggested item
                    ai_price = item.get("price", 0)
                    outfit_item = OutfitItem(
                        product_id=str(uuid.uuid4()),
                        name=name,
                        product_name=name,
                        category=std_category,
                        description=description,
                        color=color,
                        price=ai_price,
                        brand="",
                        image_url="",
                        url=""
                    )
                    
                    outfit_items.append(outfit_item)
                    total_price += ai_price
            
            except Exception as e:
                logger.error(f"Error processing item: {str(e)}")
        
        # Create brand display format
        brand_display = {}
        for category, brands in item_categories.items():
            # Format as plural if needed
            category_plural = f"{category}s" if not category.endswith('s') else category
            brand_display[category_plural] = ", ".join(brands)
        
        return outfit_items, total_price, brand_display
    
    async def _add_collage_to_outfit(self, outfit: Outfit) -> None:
        """Generate and add collage to outfit."""
        try:
            # Prepare items for collage generation
            collage_items = []
            for item in outfit.items:
                if item.image_url:
                    collage_items.append({
                        "image_url": item.image_url,
                        "category": item.category,
                        "source_url": item.url or ""
                    })
            
            # Generate collage if we have items with images
            if collage_items:
                collage_result = collage_service.create_outfit_collage(collage_items)
                outfit.collage_image = collage_result.get("collage_base64")
                outfit.image_map = collage_result.get("image_map")
        
        except Exception as e:
            logger.error(f"Error creating collage: {str(e)}")
    
    def _standardize_category(self, category: str) -> str:
        """Standardize category names for better search results."""
        category = category.lower()
        
        if any(word in category for word in ["top", "shirt", "blouse", "sweater", "sweatshirt", "t-shirt", "tee", "tank"]):
            return "Top"
        elif any(word in category for word in ["bottom", "pant", "jean", "short", "skirt", "trouser"]):
            return "Bottom"
        elif any(word in category for word in ["dress", "gown", "jumpsuit", "romper"]):
            return "Dress"
        elif any(word in category for word in ["shoe", "sneaker", "boot", "heel", "sandal", "slipper", "loafer"]):
            return "Shoes"
        elif any(word in category for word in ["jacket", "coat", "blazer", "outerwear"]):
            return "Outerwear"
        elif any(word in category for word in ["accessory", "jewelry", "watch", "bag", "purse", "scarf", "hat", "belt"]):
            return "Accessory"
        else:
            return "Other"
    
    def _get_mock_outfit_data(self, request: OutfitGenerateRequest) -> Dict[str, Any]:
        """Generate mock outfit data when API calls fail."""
        gender = request.gender.lower() if request.gender else "unisex"
        
        if gender == "male":
            return {
                "outfits": [
                    {
                        "outfit_name": "Smart Casual Weekend Outfit",
                        "description": "A versatile smart-casual outfit perfect for weekend activities. The blue button-down shirt pairs well with the chinos, creating a put-together look that's not too formal.",
                        "occasion": "Casual",
                        "items": [
                            {
                                "category": "Top",
                                "name": "Blue Oxford Button-Down Shirt",
                                "description": "Light blue cotton oxford shirt with button-down collar",
                                "color": "Blue",
                                "price": 59.99
                            },
                            {
                                "category": "Bottom",
                                "name": "Khaki Chinos",
                                "description": "Slim-fit khaki cotton chinos with a slight stretch",
                                "color": "Khaki",
                                "price": 49.99
                            },
                            {
                                "category": "Shoes",
                                "name": "Brown Leather Sneakers",
                                "description": "Minimalist brown leather sneakers with white soles",
                                "color": "Brown",
                                "price": 89.99
                            },
                            {
                                "category": "Accessory",
                                "name": "Leather Belt",
                                "description": "Brown leather belt with a brushed silver buckle",
                                "color": "Brown",
                                "price": 35.99
                            }
                        ]
                    }
                ]
            }
        else:
            return {
                "outfits": [
                    {
                        "outfit_name": "Casual Chic Summer Outfit",
                        "description": "A comfortable yet stylish summer outfit perfect for brunch or casual outings. The white top pairs nicely with the denim shorts, while the sandals and sunglasses add a touch of elegance.",
                        "occasion": "Casual",
                        "items": [
                            {
                                "category": "Top",
                                "name": "White Cotton T-shirt",
                                "description": "Loose-fitting white cotton t-shirt with a rounded neckline",
                                "color": "White",
                                "price": 24.99
                            },
                            {
                                "category": "Bottom",
                                "name": "Denim Shorts",
                                "description": "Medium wash high-waisted denim shorts with a raw hem",
                                "color": "Blue",
                                "price": 39.99
                            },
                            {
                                "category": "Shoes",
                                "name": "Tan Leather Sandals",
                                "description": "Tan leather flat sandals with ankle straps",
                                "color": "Tan",
                                "price": 59.99
                            },
                            {
                                "category": "Accessory",
                                "name": "Round Sunglasses",
                                "description": "Gold-framed round sunglasses with brown lenses",
                                "color": "Gold",
                                "price": 29.99
                            }
                        ]
                    }
                ]
            }

# Create a singleton instance
outfit_service = OutfitService() 