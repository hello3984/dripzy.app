"""
Service for generating outfit recommendations using the Anthropic API and SerpAPI.
"""

import json
import logging
import os
import random
import re
from typing import List, Dict, Any, Optional, Tuple

from anthropic import Anthropic
from anthropic.types import MessageParam
from app.modules.outfit.models import OutfitItem, Outfit, OutfitGenerateRequest, OutfitGenerateResponse
from app.services.serpapi_service import SerpApiService
from app.services.collage_service import CollageService

logger = logging.getLogger(__name__)

class OutfitService:
    """
    Service for generating outfit recommendations using the Anthropic API and SerpAPI.
    Processes user prompts to create complete outfit recommendations, including real
    product suggestions and visual collages.
    """

    def __init__(self, serpapi_service: SerpApiService, collage_service: CollageService):
        """
        Initialize the OutfitService with required dependencies.

        Args:
            serpapi_service: Service for searching real products
            collage_service: Service for creating outfit collages
        """
        self.serpapi_service = serpapi_service
        self.collage_service = collage_service
        
        # Initialize Anthropic client if API key is set
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.client = None
        if self.anthropic_api_key:
            self.client = Anthropic(api_key=self.anthropic_api_key)
        
        # Load system prompt for AI fashion stylist
        self.system_prompt = """
        You are an AI fashion stylist. Analyze the user's prompt and generate an outfit recommendation.
        
        Follow these steps:
        1. Analyze the user's prompt for style preferences, occasions, weather conditions, etc.
        2. Generate a cohesive outfit concept based on the prompt.
        3. Output a detailed outfit recommendation with specific items.
        
        Format your response in JSON with the following structure:
        {
            "occasion": "Description of the occasion or purpose of the outfit",
            "description": "Overall description of the outfit and how items work together",
            "items": [
                {
                    "category": "Top/Bottom/Shoes/Accessory/etc.",
                    "name": "Specific name of the item",
                    "description": "Detailed description including color, material, style, etc."
                },
                // Additional items...
            ],
            "color_palette": ["color1", "color2", ...],
            "style_tags": ["tag1", "tag2", ...]
        }
        
        Be specific in your item descriptions so they can be matched to real products.
        """

    def generate_outfit(self, request: OutfitGenerateRequest) -> OutfitGenerateResponse:
        """
        Generate an outfit based on the user's request.
        
        Args:
            request: The outfit generation request containing prompt, gender, and budget
            
        Returns:
            OutfitGenerateResponse: The generated outfit with product suggestions
        """
        logger.info(f"Generating outfit for prompt: {request.prompt}, gender: {request.gender}, budget: {request.budget}")
        
        try:
            if not self.client:
                logger.warning("Anthropic API key not set, using mock outfit data")
                outfit_data = self._get_mock_outfit(request.prompt, request.gender)
            else:
                # Construct the prompt with gender preference
                user_prompt = f"Generate an outfit for {request.gender} based on: {request.prompt}"
                
                # Call Anthropic API
                response = self.client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=4000,
                    temperature=0.7,
                    system=self.system_prompt,
                    messages=[
                        MessageParam(role="user", content=user_prompt)
                    ]
                )
                
                # Extract JSON from response
                outfit_data = self._extract_json(response.content[0].text)
        except Exception as e:
            logger.error(f"Error generating outfit: {e}")
            outfit_data = self._get_mock_outfit(request.prompt, request.gender)
            
        # Process the outfit data to get real products and create a collage
        return self._process_outfit_data(outfit_data, request)
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """
        Extract JSON data from the API response text.
        
        Args:
            text: Text response from the Anthropic API
            
        Returns:
            Dict containing the parsed JSON data
        """
        try:
            # Find JSON pattern in the text
            json_pattern = r'```json\s*([\s\S]*?)\s*```|(\{[\s\S]*?\})'
            match = re.search(json_pattern, text)
            
            if match:
                json_str = match.group(1) or match.group(2)
                return json.loads(json_str)
            else:
                # If no JSON block found, try to parse the entire text as JSON
                return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to extract JSON from API response: {e}")
            return {}
    
    def _process_outfit_data(self, outfit_data: Dict[str, Any], request: OutfitGenerateRequest) -> OutfitGenerateResponse:
        """
        Process outfit data, search for real products, and create a collage.
        
        Args:
            outfit_data: Raw outfit data from the Anthropic API
            request: Original outfit generation request
            
        Returns:
            OutfitGenerateResponse: Processed outfit response with real products
        """
        logger.info("Processing outfit data and searching for real products")
        
        # Extract outfit details
        occasion = outfit_data.get("occasion", "Casual outing")
        description = outfit_data.get("description", "A stylish and comfortable outfit")
        items_data = outfit_data.get("items", [])
        color_palette = outfit_data.get("color_palette", [])
        style_tags = outfit_data.get("style_tags", [])
        
        # Process each item to get real product suggestions
        processed_items = []
        image_map = {}
        
        for item_data in items_data:
            category = self._standardize_category(item_data.get("category", ""))
            name = item_data.get("name", "")
            description = item_data.get("description", "")
            
            # Skip if category is not recognized
            if not category:
                continue
                
            # Create search query based on item details and gender
            search_query = self._create_search_query(
                category=category,
                details=f"{name} {description}",
                gender=request.gender
            )
            
            # Search for real products
            try:
                price_range = None
                if request.budget:
                    # Adjust per-item budget based on category importance
                    category_budget_factors = {
                        "Top": 0.3,
                        "Bottom": 0.3,
                        "Dress": 0.6,
                        "Shoes": 0.25,
                        "Accessory": 0.15,
                        "Outerwear": 0.4
                    }
                    factor = category_budget_factors.get(category, 0.25)
                    max_item_price = request.budget * factor
                    price_range = (0, max_item_price)
                
                product = self.serpapi_service.search_products(
                    query=search_query,
                    category=category,
                    gender=request.gender,
                    min_price=price_range[0] if price_range else None,
                    max_price=price_range[1] if price_range else None,
                    limit=1
                )[0] if price_range else self.serpapi_service.search_products(
                    query=search_query,
                    category=category,
                    gender=request.gender,
                    limit=1
                )[0]
                
                # Create OutfitItem from product
                item = OutfitItem(
                    category=category,
                    name=product.get("title", name),
                    description=description,
                    image_url=product.get("image"),
                    purchase_url=product.get("link"),
                    price=product.get("price"),
                    brand=product.get("brand")
                )
                processed_items.append(item)
            except Exception as e:
                logger.error(f"Error searching for product: {e}")
                # Add fallback item without real product data
                item = OutfitItem(
                    category=category,
                    name=name,
                    description=description
                )
                processed_items.append(item)
        
        # Apply budget filter if specified
        if request.budget:
            processed_items = self._filter_by_budget(processed_items, request.budget)
        
        # Calculate total price
        total_price = sum(item.price or 0 for item in processed_items)
        
        # Create outfit object
        outfit = Outfit(
            occasion=occasion,
            description=description,
            items=processed_items,
            color_palette=color_palette,
            style_tags=style_tags,
            total_price=total_price
        )
        
        # Create collage if item images are available
        collage_image = None
        if all(item.image_url for item in processed_items):
            try:
                collage_result = self.collage_service.create_collage(
                    [item.image_url for item in processed_items if item.image_url],
                    [item.category for item in processed_items if item.image_url]
                )
                collage_image = collage_result.get("image")
                image_map = collage_result.get("map", {})
            except Exception as e:
                logger.error(f"Error creating collage: {e}")
        
        # Create and return response
        return OutfitGenerateResponse(
            prompt=request.prompt,
            outfit=outfit,
            collage_image=collage_image,
            image_map=image_map
        )
    
    def _standardize_category(self, category: str) -> str:
        """
        Standardize item category to one of the recognized categories.
        
        Args:
            category: Raw category string
            
        Returns:
            Standardized category string
        """
        category = category.lower().strip()
        
        # Map common category names to standard categories
        top_patterns = ["top", "shirt", "blouse", "tee", "t-shirt", "sweater", "sweatshirt", "tank"]
        bottom_patterns = ["bottom", "pant", "jean", "trouser", "short", "skirt"]
        dress_patterns = ["dress", "jumpsuit", "romper"]
        shoe_patterns = ["shoe", "sneaker", "boot", "heel", "sandal", "footwear"]
        accessory_patterns = ["accessory", "hat", "bag", "purse", "belt", "jewelry", "necklace", 
                              "bracelet", "ring", "earring", "scarf", "glasses", "watch", "sunglass"]
        outerwear_patterns = ["jacket", "coat", "blazer", "cardigan", "outerwear"]
        
        if any(pattern in category for pattern in top_patterns):
            return "Top"
        elif any(pattern in category for pattern in bottom_patterns):
            return "Bottom"
        elif any(pattern in category for pattern in dress_patterns):
            return "Dress"
        elif any(pattern in category for pattern in shoe_patterns):
            return "Shoes"
        elif any(pattern in category for pattern in accessory_patterns):
            return "Accessory"
        elif any(pattern in category for pattern in outerwear_patterns):
            return "Outerwear"
        else:
            # Default to a general category if no match found
            return "Accessory"
    
    def _create_search_query(self, category: str, details: str, gender: str) -> str:
        """
        Create a search query for SerpAPI based on item details.
        
        Args:
            category: Standardized category of the item
            details: Description of the item
            gender: Gender preference (male, female, unisex)
            
        Returns:
            Search query string optimized for product search
        """
        # Extract key features from details
        color_patterns = [
            "white", "black", "gray", "grey", "blue", "navy", "red", "green", 
            "yellow", "purple", "orange", "pink", "brown", "tan", "beige", "cream"
        ]
        
        material_patterns = [
            "cotton", "linen", "silk", "wool", "cashmere", "polyester", "nylon", 
            "leather", "suede", "denim", "jersey", "velvet", "satin"
        ]
        
        # Extract color and material if mentioned
        colors = [color for color in color_patterns if color in details.lower()]
        materials = [material for material in material_patterns if material in details.lower()]
        
        # Construct query
        query_parts = []
        
        # Add gender if relevant
        if gender.lower() not in ["unisex", "any", ""]:
            query_parts.append(f"{gender}")
        
        # Add color if found
        if colors:
            query_parts.append(colors[0])
        
        # Add material if found
        if materials:
            query_parts.append(materials[0])
        
        # Add category-specific terms
        if category == "Top":
            query_parts.append("shirt" if "shirt" in details.lower() else "top")
        elif category == "Bottom":
            if "jean" in details.lower():
                query_parts.append("jeans")
            elif "trouser" in details.lower() or "pant" in details.lower():
                query_parts.append("pants")
            elif "skirt" in details.lower():
                query_parts.append("skirt")
            else:
                query_parts.append("bottom")
        else:
            query_parts.append(category.lower())
        
        # Combine and return final query
        return " ".join(query_parts)
    
    def _get_mock_outfit(self, prompt: str, gender: str) -> Dict[str, Any]:
        """
        Generate mock outfit data when the API is unavailable.
        
        Args:
            prompt: User prompt
            gender: Gender preference
            
        Returns:
            Dict containing mock outfit data
        """
        logger.info("Generating mock outfit data")
        
        # Define mock outfits based on gender
        male_outfits = [
            {
                "occasion": "Casual day out",
                "description": "A comfortable and stylish casual outfit perfect for everyday wear",
                "items": [
                    {
                        "category": "Top",
                        "name": "Classic Cotton T-Shirt",
                        "description": "White cotton t-shirt with a crew neck and short sleeves"
                    },
                    {
                        "category": "Bottom",
                        "name": "Straight-Leg Jeans",
                        "description": "Medium wash straight-leg jeans with a comfortable fit"
                    },
                    {
                        "category": "Shoes",
                        "name": "Canvas Sneakers",
                        "description": "White canvas low-top sneakers with rubber soles"
                    },
                    {
                        "category": "Accessory",
                        "name": "Minimalist Watch",
                        "description": "Stainless steel watch with a black leather strap"
                    }
                ],
                "color_palette": ["White", "Blue", "Black"],
                "style_tags": ["casual", "minimalist", "everyday"]
            },
            {
                "occasion": "Business casual",
                "description": "A professional yet comfortable outfit for the office or meetings",
                "items": [
                    {
                        "category": "Top",
                        "name": "Oxford Button-Down Shirt",
                        "description": "Light blue oxford cotton button-down shirt"
                    },
                    {
                        "category": "Bottom",
                        "name": "Chino Trousers",
                        "description": "Khaki cotton chino trousers with a slim fit"
                    },
                    {
                        "category": "Shoes",
                        "name": "Leather Loafers",
                        "description": "Brown leather penny loafers with a polished finish"
                    },
                    {
                        "category": "Accessory",
                        "name": "Leather Belt",
                        "description": "Brown leather belt with a brass buckle"
                    }
                ],
                "color_palette": ["Blue", "Khaki", "Brown"],
                "style_tags": ["business casual", "professional", "smart"]
            }
        ]
        
        female_outfits = [
            {
                "occasion": "Casual day out",
                "description": "A comfortable and stylish casual outfit perfect for everyday wear",
                "items": [
                    {
                        "category": "Top",
                        "name": "Oversized Sweater",
                        "description": "Beige oversized knit sweater with a relaxed fit"
                    },
                    {
                        "category": "Bottom",
                        "name": "High-Waisted Jeans",
                        "description": "Blue high-waisted straight-leg jeans"
                    },
                    {
                        "category": "Shoes",
                        "name": "Ankle Boots",
                        "description": "Black leather ankle boots with a low heel"
                    },
                    {
                        "category": "Accessory",
                        "name": "Crossbody Bag",
                        "description": "Small black leather crossbody bag with gold hardware"
                    }
                ],
                "color_palette": ["Beige", "Blue", "Black"],
                "style_tags": ["casual", "comfortable", "chic"]
            },
            {
                "occasion": "Business casual",
                "description": "A professional yet stylish outfit for the office or meetings",
                "items": [
                    {
                        "category": "Top",
                        "name": "Silk Blouse",
                        "description": "Cream silk blouse with a v-neck and long sleeves"
                    },
                    {
                        "category": "Bottom",
                        "name": "Pencil Skirt",
                        "description": "Black knee-length pencil skirt with a back slit"
                    },
                    {
                        "category": "Shoes",
                        "name": "Pointed Heels",
                        "description": "Black leather pointed-toe heels with a moderate height"
                    },
                    {
                        "category": "Accessory",
                        "name": "Structured Tote",
                        "description": "Burgundy structured leather tote bag with laptop compartment"
                    }
                ],
                "color_palette": ["Cream", "Black", "Burgundy"],
                "style_tags": ["business casual", "professional", "elegant"]
            }
        ]
        
        # Select outfit based on gender
        if gender.lower() in ["male", "men", "man", "boy"]:
            outfit = random.choice(male_outfits)
        else:
            outfit = random.choice(female_outfits)
            
        return outfit
    
    def _filter_by_budget(self, items: List[OutfitItem], budget: float) -> List[OutfitItem]:
        """
        Filter items to fit within the specified budget.
        
        Args:
            items: List of outfit items
            budget: Maximum total budget
            
        Returns:
            Filtered list of items within budget
        """
        if not budget or not items:
            return items
            
        # Sort items by importance
        category_importance = {
            "Top": 1,
            "Bottom": 2,
            "Dress": 1,
            "Shoes": 3,
            "Outerwear": 4,
            "Accessory": 5
        }
        
        sorted_items = sorted(items, key=lambda x: category_importance.get(x.category, 10))
        
        # Keep adding items until budget is reached
        result = []
        current_total = 0
        
        for item in sorted_items:
            if item.price is None or current_total + item.price <= budget:
                result.append(item)
                current_total += item.price or 0
                
        return result 