"""
Service layer for outfit generation and management.
"""

import json
import os
import time
import uuid
from typing import Dict, List, Optional, Union

import anthropic
from dotenv import load_dotenv
from fastapi import HTTPException
from loguru import logger

from app.modules.outfit.models import Outfit, OutfitGenerateRequest, OutfitGenerateResponse, OutfitItem
from app.modules.outfit.prompts import SPECIAL_OCCASION_PROMPTS, SYSTEM_PROMPT
from app.services.collage_service import CollageService
from app.services.serpapi_service import SerpApiService

load_dotenv()

class OutfitService:
    """Service for generating and managing outfits."""
    
    def __init__(self):
        """Initialize the outfit service with necessary dependencies."""
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.anthropic_client = None
        if self.anthropic_api_key:
            self.anthropic_client = anthropic.Anthropic(api_key=self.anthropic_api_key)
        
        self.serpapi_service = SerpApiService()
        self.collage_service = CollageService()
        self.outfit_cache = {}  # Simple in-memory cache
        
    async def generate_outfit(self, request: OutfitGenerateRequest) -> OutfitGenerateResponse:
        """
        Generate an outfit based on the user's request.
        
        Args:
            request: The outfit generation request containing prompt, gender, budget, etc.
            
        Returns:
            An outfit generation response containing the generated outfit.
        """
        start_time = time.time()
        
        # Check if we have a cached response for this request
        cache_key = f"{request.prompt}_{request.gender}_{request.budget}"
        if cache_key in self.outfit_cache:
            logger.info(f"Using cached outfit for: {request.prompt}")
            cached_response = self.outfit_cache[cache_key]
            # Update processing time
            cached_response.processing_time = time.time() - start_time
            return cached_response
        
        # Determine if this is a special occasion request
        occasion_key = self._identify_occasion(request.prompt)
        
        # Generate outfit using Anthropic API
        try:
            outfit_data = await self._generate_outfit_with_anthropic(request, occasion_key)
            outfit = self._create_outfit_from_data(outfit_data)
            
            # Apply budget filter if specified
            if request.budget and request.budget > 0:
                outfit = self._apply_budget_filter(outfit, request.budget)
            
            # Source real products
            outfit = await self._source_real_products(outfit, request.gender, request.budget)
            
            # Generate collage
            outfit = await self._generate_outfit_collage(outfit)
            
            response = OutfitGenerateResponse(
                outfit=outfit,
                prompt=request.prompt,
                processing_time=time.time() - start_time
            )
            
            # Cache the response
            self.outfit_cache[cache_key] = response
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating outfit: {str(e)}")
            # Fallback to mock data in case of failure
            mock_outfit = self._generate_mock_outfit(request)
            
            return OutfitGenerateResponse(
                outfit=mock_outfit,
                prompt=request.prompt,
                processing_time=time.time() - start_time
            )
    
    def _identify_occasion(self, prompt: str) -> Optional[str]:
        """
        Identify if the prompt matches a special occasion.
        
        Args:
            prompt: The user's outfit request prompt.
            
        Returns:
            The occasion key if matched, None otherwise.
        """
        prompt_lower = prompt.lower()
        
        # Check for special occasions
        for occasion in SPECIAL_OCCASION_PROMPTS:
            if occasion in prompt_lower:
                return occasion
                
        return None
    
    async def _generate_outfit_with_anthropic(self, request: OutfitGenerateRequest, occasion_key: Optional[str]) -> Dict:
        """
        Generate outfit data using the Anthropic API.
        
        Args:
            request: The outfit generation request.
            occasion_key: Optional occasion key for special prompts.
            
        Returns:
            The generated outfit data as a dictionary.
        """
        if not self.anthropic_client:
            raise HTTPException(status_code=500, detail="Anthropic API key not configured")
        
        # Prepare the user prompt
        user_prompt = request.prompt
        if occasion_key and occasion_key in SPECIAL_OCCASION_PROMPTS:
            # Use the special occasion prompt with gender formatting
            user_prompt = SPECIAL_OCCASION_PROMPTS[occasion_key].format(gender=request.gender)
            
            # Add the original prompt for context
            user_prompt += f"\n\nOriginal request: {request.prompt}"
            
        # Add budget constraint if specified
        if request.budget and request.budget > 0:
            user_prompt += f"\n\nThe total outfit should stay within a budget of ${request.budget}."
        
        try:
            # Make the API call to Anthropic
            response = await self.anthropic_client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=2000,
                temperature=0.7,
                system=SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            # Extract JSON from the response
            content = response.content[0].text
            
            # Handle potential JSON extraction
            try:
                # Try to parse directly
                outfit_data = json.loads(content)
            except json.JSONDecodeError:
                # If direct parsing fails, try to extract JSON from markdown code block
                import re
                json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
                if json_match:
                    outfit_data = json.loads(json_match.group(1))
                else:
                    # If still no JSON, raise an error
                    raise ValueError("Could not extract valid JSON from Anthropic response")
            
            return outfit_data
            
        except Exception as e:
            logger.error(f"Error with Anthropic API: {str(e)}")
            raise
    
    def _create_outfit_from_data(self, data: Dict) -> Outfit:
        """
        Create an Outfit object from the raw data.
        
        Args:
            data: Raw outfit data from Anthropic.
            
        Returns:
            An Outfit object.
        """
        # Create OutfitItem objects from the items data
        items = []
        for item_data in data.get("items", []):
            item = OutfitItem(
                name=item_data.get("name", "Unknown Item"),
                category=item_data.get("category", "Unknown"),
                price=float(item_data.get("price", 0)),
                description=item_data.get("description", ""),
                color=item_data.get("color", ""),
                image_url=None,  # Will be filled when sourcing real products
                product_url=None  # Will be filled when sourcing real products
            )
            items.append(item)
        
        # Calculate total price
        total_price = sum(item.price for item in items)
        
        # Create and return the Outfit object
        return Outfit(
            id=str(uuid.uuid4()),
            name=data.get("name", "Custom Outfit"),
            description=data.get("description", ""),
            occasion=data.get("occasion", "Casual"),
            items=items,
            style_tags=[],  # Can be extracted or generated later
            collage_image=None,  # Will be generated later
            image_map={},  # Will be generated later
            total_price=total_price
        )
    
    def _apply_budget_filter(self, outfit: Outfit, budget: float) -> Outfit:
        """
        Apply budget constraints to the outfit by adjusting prices if needed.
        
        Args:
            outfit: The original outfit.
            budget: The maximum budget.
            
        Returns:
            The adjusted outfit.
        """
        if outfit.total_price <= budget:
            # No adjustment needed
            return outfit
        
        # Calculate the scaling factor needed
        scaling_factor = budget / outfit.total_price
        
        # Adjust each item's price
        for item in outfit.items:
            item.price = round(item.price * scaling_factor, 2)
        
        # Update the total price
        outfit.total_price = sum(item.price for item in outfit.items)
        
        return outfit
    
    async def _source_real_products(self, outfit: Outfit, gender: str, budget: Optional[float] = None) -> Outfit:
        """
        Source real products for the outfit items using the SerpAPI service.
        
        Args:
            outfit: The outfit with items to source.
            gender: The gender to filter products by.
            budget: Optional budget constraint for individual items.
            
        Returns:
            The outfit with real product data.
        """
        sourced_items = []
        
        for item in outfit.items:
            # Calculate item budget based on the original price proportion
            item_budget = None
            if budget:
                # Allow a bit more than the AI's estimate
                item_budget = item.price * 1.2
            
            # Prepare the search query
            query = f"{gender} {item.color} {item.name}"
            
            # Source the product
            try:
                products = await self.serpapi_service.search_products(
                    query=query,
                    category=item.category,
                    gender=gender,
                    max_price=item_budget,
                    limit=1
                )
                
                if products:
                    product = products[0]
                    
                    # Update item with real product data
                    item.name = product.get("title", item.name)
                    item.price = float(product.get("price", item.price))
                    item.image_url = product.get("thumbnail", None)
                    item.product_url = product.get("link", None)
                    item.brand = product.get("brand", None)
                    
                    # If no description was provided by the product, keep the AI-generated one
                    if product.get("description"):
                        item.description = product.get("description")
            
            except Exception as e:
                logger.error(f"Error sourcing product for {item.category}: {str(e)}")
                # Keep the original item if sourcing fails
            
            sourced_items.append(item)
        
        # Update the outfit with sourced items
        outfit.items = sourced_items
        
        # Recalculate total price
        outfit.total_price = sum(item.price for item in outfit.items)
        
        return outfit
    
    async def _generate_outfit_collage(self, outfit: Outfit) -> Outfit:
        """
        Generate a collage image for the outfit.
        
        Args:
            outfit: The outfit with sourced items.
            
        Returns:
            The outfit with collage image and image map.
        """
        try:
            # Prepare items with images for collage
            items_with_images = [
                {"category": item.category, "image_url": item.image_url}
                for item in outfit.items
                if item.image_url
            ]
            
            if not items_with_images:
                logger.warning("No items with images found for collage generation")
                return outfit
            
            # Generate the collage
            collage_result = await self.collage_service.create_outfit_collage(items_with_images)
            
            if collage_result:
                outfit.collage_image = collage_result.get("collage_base64")
                outfit.image_map = collage_result.get("image_map", {})
        
        except Exception as e:
            logger.error(f"Error generating outfit collage: {str(e)}")
        
        return outfit
    
    def _generate_mock_outfit(self, request: OutfitGenerateRequest) -> Outfit:
        """
        Generate a mock outfit when the Anthropic API fails.
        
        Args:
            request: The original outfit generation request.
            
        Returns:
            A mock Outfit object.
        """
        # Define some mock items based on the prompt
        items = []
        
        # Parse the prompt for keywords
        prompt_lower = request.prompt.lower()
        
        # Determine style based on prompt
        style = "Casual"  # Default style
        if "formal" in prompt_lower or "business" in prompt_lower:
            style = "Formal"
        elif "sporty" in prompt_lower or "athletic" in prompt_lower:
            style = "Sporty"
        elif "beach" in prompt_lower or "summer" in prompt_lower:
            style = "Summer"
        elif "winter" in prompt_lower:
            style = "Winter"
        
        # Create mock items based on style and gender
        if style == "Casual":
            if request.gender.lower() == "male":
                items = [
                    OutfitItem(
                        name="Cotton T-Shirt",
                        category="Top",
                        price=25.99,
                        brand="H&M",
                        description="Classic cotton t-shirt in solid color",
                        color="White",
                        image_url="https://via.placeholder.com/150",
                        product_url="https://example.com/product1"
                    ),
                    OutfitItem(
                        name="Straight Leg Jeans",
                        category="Bottom",
                        price=59.99,
                        brand="Levi's",
                        description="Medium wash straight leg jeans",
                        color="Blue",
                        image_url="https://via.placeholder.com/150",
                        product_url="https://example.com/product2"
                    ),
                    OutfitItem(
                        name="Canvas Sneakers",
                        category="Shoes",
                        price=45.00,
                        brand="Converse",
                        description="Classic canvas sneakers",
                        color="Black",
                        image_url="https://via.placeholder.com/150",
                        product_url="https://example.com/product3"
                    )
                ]
            else:  # Female
                items = [
                    OutfitItem(
                        name="V-Neck Blouse",
                        category="Top",
                        price=29.99,
                        brand="Zara",
                        description="Lightweight v-neck blouse with short sleeves",
                        color="Light Blue",
                        image_url="https://via.placeholder.com/150",
                        product_url="https://example.com/product4"
                    ),
                    OutfitItem(
                        name="Skinny Jeans",
                        category="Bottom",
                        price=49.99,
                        brand="American Eagle",
                        description="High-waisted skinny jeans",
                        color="Dark Blue",
                        image_url="https://via.placeholder.com/150",
                        product_url="https://example.com/product5"
                    ),
                    OutfitItem(
                        name="Ankle Boots",
                        category="Shoes",
                        price=89.99,
                        brand="Steve Madden",
                        description="Leather ankle boots with low heel",
                        color="Brown",
                        image_url="https://via.placeholder.com/150",
                        product_url="https://example.com/product6"
                    )
                ]
        
        # Apply budget filter if needed
        total_price = sum(item.price for item in items)
        if request.budget and total_price > request.budget:
            scaling_factor = request.budget / total_price
            for item in items:
                item.price = round(item.price * scaling_factor, 2)
            total_price = sum(item.price for item in items)
        
        return Outfit(
            id=str(uuid.uuid4()),
            name=f"{style} Outfit",
            description=f"A {style.lower()} outfit generated based on your request.",
            occasion=style,
            items=items,
            style_tags=[style.lower(), request.gender.lower()],
            collage_image=None,
            image_map={},
            total_price=total_price
        )

# Create an instance of the service
outfit_service = OutfitService() 