import asyncio
import json
import logging
import os
import random
import re
import sys
import time
from typing import Dict, List, Any, Optional

import httpx
from fastapi import HTTPException

from app.core.cache import cache_service

# Configure logging
logger = logging.getLogger(__name__)

class SerpAPIService:
    """Service for searching products using SerpAPI."""
    
    def __init__(self):
        """Initialize SerpAPI service with API key and cache."""
        self.api_key = os.getenv("SERPAPI_API_KEY")
        if not self.api_key:
            logger.warning("SERPAPI_API_KEY not found in environment variables. Using fallback data.")
        
        # Initialize cache with configurable TTL
        self.short_cache_ttl = int(os.getenv("CACHE_TTL_SHORT", "300"))  # 5 minutes
        self.medium_cache_ttl = int(os.getenv("CACHE_TTL_MEDIUM", "3600"))  # 1 hour
        self.long_cache_ttl = int(os.getenv("CACHE_TTL_LONG", "86400"))  # 24 hours
        
        # URL for SerpAPI searches
        self.search_url = "https://serpapi.com/search"
        
        # Track rate limiting
        self.rate_limited = False
        self.rate_limit_reset = 0
        
    async def search_products(self, query: str, category: Optional[str] = None, 
                        gender: Optional[str] = None, limit: int = 10, 
                        min_price: Optional[float] = None, 
                        max_price: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Search for products using SerpAPI with improved caching and error handling.
        
        Args:
            query: Search query
            category: Product category
            gender: Gender filter
            limit: Maximum number of results
            min_price: Minimum price
            max_price: Maximum price
            
        Returns:
            List of product data
        """
        # Create a cache key for this query
        cache_key = f"products_{query}_{category}_{gender}_{min_price}_{max_price}_{limit}"
        
        # Check if we have cached results
        cached_results = cache_service.get(cache_key, "medium")
        if cached_results:
            logger.info(f"Using cached products for {query}")
            return cached_results
            
        # Check for similar queries in cache
        similar_products = self._find_similar_cached_query(query, category, gender)
        if similar_products:
            logger.info(f"Using similar cached products for {query}")
            return similar_products
            
        # If we're rate limited, wait before trying again
        if self.rate_limited and time.time() < self.rate_limit_reset:
            waiting_time = self.rate_limit_reset - time.time()
            logger.warning(f"Rate limited. Waiting {waiting_time:.1f} seconds before retry.")
            # Return cached products from any similar query if available
            all_cached = self._get_any_cached_product(category)
            if all_cached:
                return all_cached
                
        # Try multiple attempts with exponential backoff
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                # Build search query with gender if provided
                search_term = query
                if gender and gender != "unisex":
                    search_term = f"{gender}'s {search_term}"
                if category:
                    search_term = f"{search_term} {category}"
                
                # Additional parameters for search filtering
                params = {
                    "api_key": self.api_key,
                    "engine": "google_shopping",
                    "q": search_term,
                    "num": limit,
                    "google_domain": "google.com",
                    "gl": "us",
                    "hl": "en",
                    "tbm": "shop",
                    "tbs": "mr:1",  # Sort by relevance
                }
                
                # Add price range if provided
                if min_price:
                    params["tbs"] += f",price:1,ppr_min:{min_price}"
                if max_price:
                    params["tbs"] += f",ppr_max:{max_price}"
                
                # Make request to SerpAPI
                logger.info(f"Searching SerpAPI for: {search_term}")
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(self.search_url, params=params)
                
                # Handle different response codes
                if response.status_code == 200:
                    self.rate_limited = False
                    data = response.json()
                    
                    # Extract shopping results
                    if "shopping_results" in data and data["shopping_results"]:
                        products = self._format_products(data["shopping_results"], category)
                        # Cache the results
                        cache_service.set(cache_key, products, "medium")
                        # Also cache with simpler key for similarity matching
                        simple_key = f"query_{query}_{category}"
                        cache_service.set(simple_key, products, "medium")
                        return products
                    else:
                        logger.warning(f"No shopping results found for '{search_term}'")
                        
                elif response.status_code == 429:  # Rate limited
                    # Set rate limiting info
                    self.rate_limited = True
                    # Reset after 60 seconds or use header if available
                    retry_after = response.headers.get("Retry-After", "60")
                    self.rate_limit_reset = time.time() + int(retry_after)
                    logger.error(f"Error searching products with SerpAPI: 429 Rate Limited. Retry after {retry_after}s")
                    
                    # Exponential backoff
                    if attempt < max_attempts - 1:
                        wait_time = 2 ** attempt
                        logger.info(f"Retrying in {wait_time} seconds (attempt {attempt+1}/{max_attempts})")
                        await asyncio.sleep(wait_time)
                    else:
                        # On last attempt, try to find any cached product for the category
                        all_cached = self._get_any_cached_product(category)
                        if all_cached:
                            logger.info(f"Using alternate cached products for {category}")
                            return all_cached
                            
                        # If no cached products, log and continue to fallback
                        logger.warning(f"Using fallback products for {category}: {query}")
                        products = self._get_fallback_products(category, query)
                        # Mark them as fallbacks but still cache them
                        for product in products:
                            product["product_id"] = f"fallback_{product['product_id']}"
                            product["fallback_reason"] = "Rate limited"
                        
                        cache_service.set(cache_key, products, "short")  # Short cache for fallbacks
                        return products
                else:
                    # Other error
                    logger.error(f"SerpAPI error: {response.status_code} - {response.text}")
                    if attempt < max_attempts - 1:
                        wait_time = 2 ** attempt
                        logger.info(f"Retrying in {wait_time} seconds (attempt {attempt+1}/{max_attempts})")
                        await asyncio.sleep(wait_time)
                    
            except Exception as e:
                logger.error(f"Error searching products with SerpAPI: {str(e)}")
                if attempt < max_attempts - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds (attempt {attempt+1}/{max_attempts})")
                    await asyncio.sleep(wait_time)
        
        # If we reach here, all attempts failed - use fallback with clear marking
        logger.warning(f"Using fallback products for {category}: {query}")
        products = self._get_fallback_products(category, query)
        # Mark them as fallbacks
        for product in products:
            product["product_id"] = f"fallback_{product['product_id']}"
            product["fallback_reason"] = "All API attempts failed"
            
        cache_service.set(cache_key, products, "short")  # Short cache for fallbacks
        return products
        
    def _format_products(self, results: List[Dict[str, Any]], category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Format raw API results into standardized product format."""
        products = []
        
        for item in results:
            # Extract price as a float
            price_str = item.get("price", "0")
            price = 0.0
            
            # Parse price from string (remove currency symbol and commas)
            if isinstance(price_str, str):
                price_match = re.search(r'[\d,]+\.\d+', price_str)
                if price_match:
                    price = float(price_match.group().replace(',', ''))
            
            # Create product object
            product = {
                "product_id": str(item.get("product_id", item.get("position", ""))),
                "product_name": item.get("title", "Product"),
                "brand": item.get("merchant", "Various"),
                "category": category or self._detect_category(item.get("title", "")),
                "price": price,
                "url": item.get("link", ""),
                "image_url": item.get("thumbnail", ""),
                "source": "Google Shopping",
                "description": item.get("snippet", "")
            }
            
            products.append(product)
            
        return products
    
    def _detect_category(self, title: str) -> str:
        """Detect product category from title."""
        title_lower = title.lower()
        
        if any(word in title_lower for word in ["shirt", "top", "tee", "blouse", "sweater", "hoodie"]):
            return "Top"
        elif any(word in title_lower for word in ["pants", "jeans", "shorts", "skirt", "leggings", "trouser"]):
            return "Bottom"
        elif any(word in title_lower for word in ["dress", "gown"]):
            return "Dress"
        elif any(word in title_lower for word in ["shoes", "sneakers", "boots", "sandals"]):
            return "Shoes"
        elif any(word in title_lower for word in ["jacket", "coat", "blazer", "outerwear"]):
            return "Outerwear"
        elif any(word in title_lower for word in ["hat", "cap", "beanie", "scarf", "gloves", "accessory", 
                                               "watch", "necklace", "earrings", "bracelet", "bag", "purse"]):
            return "Accessory"
        else:
            return "Other"
    
    def _find_similar_cached_query(self, query: str, category: Optional[str], gender: Optional[str]) -> List[Dict[str, Any]]:
        """Find similar cached queries to avoid repeating API calls."""
        # Try a few variations of the query for cache hits
        query_lower = query.lower()
        variations = [
            f"query_{query_lower}_{category}",
            f"query_{query_lower}",
        ]
        
        # If gender is specified, add gender-specific variants
        if gender and gender != "unisex":
            variations.append(f"query_{gender}'s {query_lower}_{category}")
        
        # Check if we have any of these in cache
        for var in variations:
            cached = cache_service.get(var, "medium")
            if cached:
                return cached
                
        return []
    
    def _get_any_cached_product(self, category: Optional[str]) -> List[Dict[str, Any]]:
        """Find any cached products that match the category as a fallback."""
        # Get all cached items
        all_cache = cache_service._cache.items()
        
        # Filter for product caches that match category
        for key, entry in all_cache:
            if key.startswith("products_") and category and category.lower() in key.lower():
                return entry["data"]
                
        return []
        
    def _get_fallback_products(self, category: Optional[str], query: str) -> List[Dict[str, Any]]:
        """Generate fallback products when API fails."""
        fallback_products = []
        
        # Base product template
        base_product = {
            "product_id": f"fallback_{random.randint(1000, 9999)}",
            "brand": "Sample Brand",
            "price": 49.99,
            "url": "",
            "source": "Fallback Data",
            "description": f"This is a fallback product for when the API is unavailable. Search was for: {query}"
        }
        
        # Create category-specific fallbacks
        if category == "Top" or not category:
            fallback_products.append({
                **base_product,
                "product_id": f"fallback_top_{random.randint(1000, 9999)}",
                "product_name": f"Stylish {query} T-Shirt",
                "category": "Top",
                "image_url": "https://via.placeholder.com/300x400?text=T-Shirt",
            })
            fallback_products.append({
                **base_product,
                "product_id": f"fallback_top_{random.randint(1000, 9999)}",
                "product_name": f"Casual {query} Sweater",
                "category": "Top",
                "price": 59.99,
                "image_url": "https://via.placeholder.com/300x400?text=Sweater",
            })
        
        if category == "Bottom" or not category:
            fallback_products.append({
                **base_product,
                "product_id": f"fallback_bottom_{random.randint(1000, 9999)}",
                "product_name": f"Classic {query} Jeans",
                "category": "Bottom",
                "price": 69.99,
                "image_url": "https://via.placeholder.com/300x400?text=Jeans",
            })
            fallback_products.append({
                **base_product,
                "product_id": f"fallback_bottom_{random.randint(1000, 9999)}",
                "product_name": f"Casual {query} Shorts",
                "category": "Bottom",
                "price": 39.99,
                "image_url": "https://via.placeholder.com/300x400?text=Shorts",
            })
            
        if category == "Shoes" or not category:
            fallback_products.append({
                **base_product,
                "product_id": f"fallback_shoes_{random.randint(1000, 9999)}",
                "product_name": f"Comfortable {query} Sneakers",
                "category": "Shoes",
                "price": 89.99,
                "image_url": "https://via.placeholder.com/300x400?text=Sneakers",
            })
            
        if category == "Accessory" or not category:
            fallback_products.append({
                **base_product,
                "product_id": f"fallback_accessory_{random.randint(1000, 9999)}",
                "product_name": f"Stylish {query} Watch",
                "category": "Accessory",
                "price": 129.99,
                "image_url": "https://via.placeholder.com/300x400?text=Watch",
            })
            
        if category == "Outerwear" or not category:
            fallback_products.append({
                **base_product,
                "product_id": f"fallback_outerwear_{random.randint(1000, 9999)}",
                "product_name": f"Winter {query} Jacket",
                "category": "Outerwear",
                "price": 149.99,
                "image_url": "https://via.placeholder.com/300x400?text=Jacket",
            })
            
        if category == "Dress" or not category:
            fallback_products.append({
                **base_product,
                "product_id": f"fallback_dress_{random.randint(1000, 9999)}",
                "product_name": f"Elegant {query} Dress",
                "category": "Dress",
                "price": 99.99,
                "image_url": "https://via.placeholder.com/300x400?text=Dress",
            })
            
        # If we still don't have products, add some generic ones
        if not fallback_products:
            for i in range(3):
                fallback_products.append({
                    **base_product,
                    "product_id": f"fallback_generic_{random.randint(1000, 9999)}",
                    "product_name": f"Generic {query} Item {i+1}",
                    "category": category or "Other",
                    "price": random.uniform(29.99, 199.99),
                    "image_url": f"https://via.placeholder.com/300x400?text=Item+{i+1}",
                })
                
        return fallback_products

# Create a singleton instance
serpapi_service = SerpAPIService() 