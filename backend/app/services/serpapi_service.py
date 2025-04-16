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
import aiohttp

from app.core.cache import cache_service
from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

class SerpAPIService:
    """Service for searching products using SerpAPI."""
    
    def __init__(self):
        """Initialize SerpAPI service with API key and cache."""
        self.api_key = os.environ.get("SERPAPI_API_KEY")
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
        
    async def test_api_key(self) -> bool:
        """
        Test if the SerpAPI key is valid by making a simple test request.
        Returns True if valid, False otherwise.
        """
        if not self.api_key:
            logger.warning("No SerpAPI key configured")
            return False
        
        try:
            # Make a minimal request to test the API key
            params = {
                "engine": "google",
                "q": "test query",
                "api_key": self.api_key,
                "num": "1"  # Request minimal results
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://serpapi.com/search", 
                    params=params
                ) as response:
                    if response.status == 200:
                        logger.info("SerpAPI key is valid")
                        return True
                    elif response.status == 429:
                        logger.warning("SerpAPI rate limit reached during test")
                        return True  # Key is valid but rate limited
                    elif response.status == 401:
                        logger.error("SerpAPI key is invalid")
                        return False
                    else:
                        logger.warning(f"Unexpected response from SerpAPI: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Error testing SerpAPI key: {str(e)}")
            return False
            
    async def search_products(
        self, 
        query: str, 
        category: Optional[str] = None,
        num_products: int = 5,
        budget: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for products using SerpAPI
        
        Args:
            query: Search query
            category: Product category
            num_products: Number of products to return
            budget: Maximum price for products
            
        Returns:
            List of product dictionaries
        """
        # Create a cache key based on the search parameters
        cache_key = f"products:{query}:{category}:{num_products}:{budget}"
        
        # Check if we have cached results
        cached_results = cache_service.get(cache_key)
        if cached_results:
            logger.info(f"Using cached results for query: {query}")
            return cached_results
            
        # If no API key, use fallback products
        if not self.api_key:
            logger.warning("No SerpAPI API key configured, using fallback products")
            return self._get_fallback_products(query, category, num_products)
            
        # Check if we're currently rate limited
        if self.rate_limited and time.time() < self.rate_limit_reset:
            wait_time = int(self.rate_limit_reset - time.time())
            logger.warning(f"Rate limited by SerpAPI, waiting {wait_time} seconds")
            
            # Use similar cached products if available while rate limited
            similar_products = self._get_similar_cached_products(query, category)
            if similar_products:
                logger.info(f"Using similar cached products for query: {query}")
                return similar_products
                
            # Wait for rate limit to reset if needed
            if wait_time < 30:  # Only wait if it's a short time
                await asyncio.sleep(wait_time + 1)
            else:
                logger.warning(f"Rate limit wait time too long ({wait_time}s), using fallback products")
                return self._get_fallback_products(query, category, num_products)
        
        # Construct the search query
        search_query = query
        if category:
            search_query = f"{category} {search_query}"
            
        # Prepare SerpAPI parameters
        params = {
            "api_key": self.api_key,
            "engine": "google_shopping",
            "google_domain": "google.com",
            "q": search_query,
            "num": num_products * 2,  # Request more to filter out irrelevant results
            "hl": "en",
            "gl": "us",
            "tbs": "mr:1",  # Merchant rated
        }
        
        if budget:
            params["tbs"] = f"{params.get('tbs', '')},pr:1,ppr_max:{int(budget)}"
            
        # Make the API request with retries
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Searching products for query: {search_query}")
                
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(self.search_url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    shopping_results = data.get("shopping_results", [])
                    
                    if not shopping_results:
                        logger.warning(f"No shopping results found for query: {search_query}")
                        return self._get_fallback_products(query, category, num_products)
                    
                    # Transform results to a standard format
                    products = []
                    for item in shopping_results[:num_products]:
                        product = {
                            "product_id": item.get("product_id", f"product_{len(products)}"),
                            "name": item.get("title", "Unknown Product"),
                            "brand": item.get("source", "Unknown Brand"),
                            "category": category or "Unknown Category",
                            "description": "",
                            "price": item.get("price", 0.0),
                            "url": item.get("link", ""),
                            "image_url": item.get("thumbnail", "")
                        }
                        
                        # Parse the price string to float
                        if isinstance(product["price"], str):
                            price_match = re.search(r'\$?([\d,]+(\.\d+)?)', product["price"])
                            if price_match:
                                product["price"] = float(price_match.group(1).replace(',', ''))
                            else:
                                product["price"] = 0.0
                                
                        products.append(product)
                    
                    # Cache the results
                    cache_service.set(cache_key, products, ttl=3600)  # Cache for 1 hour
                    
                    # Reset rate limit status
                    self.rate_limited = False
                    self.rate_limit_reset = 0
                    
                    return products
                    
                elif response.status_code == 429:
                    # Handle rate limiting
                    logger.warning("SerpAPI rate limit reached")
                    self.rate_limited = True
                    
                    # Get reset time from headers or default to 1 minute
                    retry_after = response.headers.get("Retry-After")
                    if retry_after and retry_after.isdigit():
                        self.rate_limit_reset = time.time() + int(retry_after)
                    else:
                        self.rate_limit_reset = time.time() + 60
                        
                    if attempt < max_retries - 1:
                        logger.info(f"Retrying after {retry_delay} seconds (attempt {attempt+1}/{max_retries})")
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        logger.warning("Maximum retry attempts reached, using fallback products")
                        similar_products = self._get_similar_cached_products(query, category)
                        if similar_products:
                            return similar_products
                        return self._get_fallback_products(query, category, num_products)
                        
                else:
                    logger.error(f"SerpAPI request failed with status code {response.status_code}")
                    if attempt < max_retries - 1:
                        logger.info(f"Retrying after {retry_delay} seconds (attempt {attempt+1}/{max_retries})")
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2
                    else:
                        logger.warning("Maximum retry attempts reached, using fallback products")
                        return self._get_fallback_products(query, category, num_products)
                        
            except Exception as e:
                logger.error(f"Error searching products with SerpAPI: {str(e)}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying after {retry_delay} seconds (attempt {attempt+1}/{max_retries})")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    logger.warning("Maximum retry attempts reached, using fallback products")
                    return self._get_fallback_products(query, category, num_products)
                    
        # If we get here, all retries failed
        return self._get_fallback_products(query, category, num_products)
        
    def _get_similar_cached_products(self, query: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get cached products from similar queries
        
        Args:
            query: Search query
            category: Product category
            
        Returns:
            List of similar cached products or empty list
        """
        # Look for similar cached queries
        all_cached_keys = cache_service.get_keys("products:*")
        
        # Convert query to lowercase and split into words for matching
        query_words = set(query.lower().split())
        
        for key in all_cached_keys:
            try:
                # Extract the query part from the cache key
                key_parts = key.split(':')
                if len(key_parts) >= 2:
                    cached_query = key_parts[1].lower()
                    cached_category = key_parts[2] if len(key_parts) > 2 else None
                    
                    # Check if category matches (if specified)
                    if category and cached_category and category.lower() != cached_category.lower():
                        continue
                        
                    # Check if at least half of the query words match
                    cached_query_words = set(cached_query.split())
                    common_words = query_words.intersection(cached_query_words)
                    
                    if (len(common_words) >= len(query_words) / 2 or 
                        len(common_words) >= len(cached_query_words) / 2):
                        # Get cached products for this similar query
                        similar_products = cache_service.get(key)
                        if similar_products:
                            logger.info(f"Found similar cached products for '{query}' from '{cached_query}'")
                            return similar_products
            except Exception as e:
                logger.error(f"Error processing cached key {key}: {str(e)}")
                continue
                
        return []
        
    def _get_fallback_products(self, query: str, category: Optional[str] = None, num_products: int = 5) -> List[Dict[str, Any]]:
        """
        Generate fallback products when API fails
        
        Args:
            query: Search query
            category: Product category
            num_products: Number of products to generate
            
        Returns:
            List of generated fallback products
        """
        logger.info(f"Generating fallback products for query: {query}")
        
        # Create basic categories and brands for fallback generation
        categories = ["Clothing", "Accessories", "Shoes", "Bags", "Jewelry"]
        brands = ["Fashion Brand", "Trendy Co.", "Style House", "Chic Designs", "Modern Apparel"]
        
        if not category:
            category = random.choice(categories)
            
        products = []
        for i in range(num_products):
            price = round(random.uniform(20, 200), 2)
            product = {
                "product_id": f"fallback_{int(time.time())}_{i}",
                "name": f"{query.title()} {category}",
                "brand": random.choice(brands),
                "category": category,
                "description": f"A stylish {query.lower()} {category.lower()} for your wardrobe.",
                "price": price,
                "url": "https://example.com/product",
                "image_url": f"https://placehold.co/400x600?text={query.replace(' ', '+')}"
            }
            products.append(product)
            
        return products

# Create a singleton instance
serpapi_service = SerpAPIService() 