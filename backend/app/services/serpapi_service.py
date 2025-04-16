import asyncio
import json
import logging
import os
import random
import re
import sys
import time
import ssl
import uuid
from typing import Dict, List, Any, Optional

import httpx
from fastapi import HTTPException
import aiohttp

from app.core.cache import cache_service
from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Create a secure SSL context that falls back to unverified if needed
def create_ssl_context():
    """
    Create an SSL context for secure connections.
    On some systems with SSL certificate issues, this will fall back to unverified connections.
    """
    try:
        # Try to create a default SSL context first
        context = ssl.create_default_context()
        return context
    except Exception as e:
        logger.warning(f"Could not create default SSL context: {e}")
        # Fall back to unverified context
        context = ssl._create_unverified_context()
        logger.warning("Using unverified SSL context due to certificate issues")
        return context

# Global SSL context for use in the module
ssl_context = create_ssl_context()

class SerpAPIService:
    """Service for searching products using SerpAPI."""
    
    def __init__(self, settings: Optional[Any] = None):
        """Initialize SerpAPI service with API key and cache."""
        # Prioritize key from settings if provided, otherwise try environment
        if settings and settings.SERPAPI_API_KEY:
            self.api_key = settings.SERPAPI_API_KEY
            logger.info("SerpAPI key loaded from settings.")
        else:
            self.api_key = os.environ.get("SERPAPI_API_KEY")
            logger.info("Attempted to load SerpAPI key from environment.")
        
        if not self.api_key:
            logger.warning("SERPAPI_API_KEY not found. Using fallback data.")
        
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
            
            # Disable SSL verification for SerpAPI requests
            os.environ['PYTHONHTTPSVERIFY'] = '0'
            
            # Use httpx with verification disabled
            import httpx
            
            async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
                response = await client.get(
                    "https://serpapi.com/search", 
                    params=params
                )
                
                if response.status_code == 200:
                    logger.info("SerpAPI key is valid")
                    return True
                elif response.status_code == 429:
                    logger.warning("SerpAPI rate limit reached during test")
                    return True  # Key is valid but rate limited
                elif response.status_code == 401:
                    logger.error(f"SerpAPI key is invalid: {response.text}")
                    return False
                else:
                    logger.warning(f"Unexpected response from SerpAPI: {response.status_code}")
                    try:
                        logger.warning(f"Response text: {response.text}")
                    except:
                        pass
                    return False
        except Exception as e:
            logger.error(f"Error testing SerpAPI key: {str(e)}")
            return False
            
    async def search_products(
        self, 
        query: str, 
        category: Optional[str] = None,
        num_products: int = 5,
        budget: Optional[float] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        # Remove unused parameters that cause errors but store in kwargs
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Search for products using SerpAPI
        
        Args:
            query: Search query
            category: Product category
            num_products: Number of products to return
            budget: Maximum price for products (can be used to derive min/max)
            min_price: Minimum price filter
            max_price: Maximum price filter
            **kwargs: Additional parameters (gender, etc.) that are ignored
            
        Returns:
            List of product dictionaries
        """
        # Create a cache key based on the search parameters
        cache_key = f"products:{query}:{category}:{num_products}:{budget}:{min_price}:{max_price}"
        
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
        
        # Add price filters to tbs parameter if provided
        price_filters = []
        if min_price:
            price_filters.append(f"ppr_min:{int(min_price)}")
        if max_price:
            price_filters.append(f"ppr_max:{int(max_price)}")
        
        if price_filters:
            params["tbs"] = f"{params.get('tbs', '')},pr:1,{','.join(price_filters)}"
        
        # Make the API request with retries
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Searching products for query: {search_query}")
                
                # Disable SSL verification for SerpAPI requests
                os.environ['PYTHONHTTPSVERIFY'] = '0'
                
                # Use httpx with verification disabled
                async with httpx.AsyncClient(timeout=15.0, verify=False) as client:
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
                    cache_service.set(cache_key, products)
                    
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
        
    def _get_fallback_products(self, query: str, category: str = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Generate fallback products when the API is unavailable."""
        # Log a stronger warning
        logger.warning(f"USING FALLBACK PRODUCTS FOR: {query} - Real products unavailable. This is just a placeholder!")
        
        # Only generate a single fallback product to avoid cluttering UI
        product = {
            "product_id": f"fallback_{uuid.uuid4().hex[:8]}",
            "product_name": f"{category if category else 'Item'}: {query}",
            "brand": "API Unavailable",
            "category": category or "Other",
            "description": f"This is a placeholder. {query}",
            "price": random.uniform(29.99, 39.99),
            "url": "https://example.com/product",
            "image_url": f"https://via.placeholder.com/300x400?text=No+Image",
            "fallback_reason": "API unavailable"
        }
        
        return [product]

# --- Removed global instance creation ---
# No longer create the instance here
# serpapi_service = SerpAPIService()
# --------------------------------------- 

# Create the global instance with settings
serpapi_service = SerpAPIService(settings=settings) 