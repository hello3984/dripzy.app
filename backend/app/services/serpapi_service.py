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
from app.core.connection_pool import get_connection_pool

# Configure logging
logger = logging.getLogger(__name__)

# Create a secure SSL context that falls back to unverified if needed
def create_ssl_context():
    """
    Create an SSL context for secure connections.
    On some systems with SSL certificate issues, this will fall back to unverified connections.
    """
    try:
        import ssl
        import platform
        
        # For macOS, we need a special approach to get system certificates
        if platform.system() == 'Darwin':
            try:
                # Try certifi first on macOS
                import certifi
                context = ssl.create_default_context(cafile=certifi.where())
                logger.debug("Created SSL context with certifi certificates on macOS")
                return context
            except (ImportError, Exception) as cert_error:
                logger.warning(f"Could not use certifi on macOS: {cert_error}")
                
                # Try to access macOS keychain directly
                try:
                    import subprocess
                    import tempfile
                    
                    # Extract certificates from the system keychain
                    process = subprocess.run(
                        ["/usr/bin/security", "find-certificate", "-a", "-p", 
                         "/System/Library/Keychains/SystemRootCertificates.keychain"],
                        capture_output=True, text=True, check=False
                    )
                    
                    if process.returncode == 0 and process.stdout:
                        # Create a temporary file with the certificates
                        with tempfile.NamedTemporaryFile(delete=False, mode='w') as cert_file:
                            cert_file.write(process.stdout)
                            cert_path = cert_file.name
                        
                        # Create SSL context with the temporary certificate file
                        context = ssl.create_default_context(cafile=cert_path)
                        logger.info("Created SSL context with macOS system certificates")
                        return context
                except Exception as mac_error:
                    logger.warning(f"Could not access macOS certificates: {mac_error}")
        
        # For non-macOS platforms, try certifi first
        try:
            import certifi
            context = ssl.create_default_context(cafile=certifi.where())
            logger.debug("Created SSL context with certifi certificates")
            return context
        except (ImportError, Exception) as cert_error:
            logger.warning(f"Could not use certifi: {cert_error}")
        
        # Next, try using requests' certificate bundle if available
        try:
            import requests.certs
            context = ssl.create_default_context(cafile=requests.certs.where())
            logger.debug("Created SSL context with requests certificates")
            return context
        except (ImportError, Exception) as req_error:
            logger.warning(f"Could not use requests certificates: {req_error}")
        
        # Last resort: create default context without custom certificates
        context = ssl.create_default_context()
        logger.info("Created default SSL context without custom certificates")
        return context
    except Exception as e:
        logger.warning(f"Could not create default SSL context: {e}")
        # Absolute fallback to unverified context
        try:
            context = ssl._create_unverified_context()
            logger.warning("Using unverified SSL context due to certificate issues")
            return context
        except Exception as fatal_error:
            logger.error(f"Critical SSL context creation failure: {fatal_error}")
            raise RuntimeError("Cannot create any SSL context") from fatal_error

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
        gender: Optional[str] = None,  # We'll explicitly accept this but not use it
        limit: Optional[int] = None,   # Accept but not use this parameter
        **kwargs  # Accept any additional parameters
    ) -> List[Dict[str, Any]]:
        """
        Search for products using SerpAPI
        
        Args:
            query: Search query
            category: Product category
            num_products: Number of products to return
            budget: Optional budget to filter products
            min_price: Optional minimum price
            max_price: Optional maximum price
            
        Returns:
            List of product data dictionaries
        """
        # Check for rate limiting first
        if self.rate_limited and time.time() < self.rate_limit_reset:
            logger.warning(f"SerpAPI is rate limited. Using fallback data.")
            return self._get_fallback_products(category or "Top", num_products)
            
        # Create a cache key based on the search query and parameters
        cache_key = f"serpapi:products:{query}:{category}:{num_products}:{budget}:{min_price}:{max_price}"
        
        # Try to get cached results first to improve response time
        cached_results = cache_service.get(cache_key, "medium")
        if cached_results:
            logger.info(f"Using cached product results for query: {query}")
            return cached_results
            
        # If no API key, return fallback data
        if not self.api_key:
            logger.warning("No SerpAPI key. Using fallback product data.")
            return self._get_fallback_products(category or "Top", num_products)
            
        try:
            # Set up the search parameters
            params = {
                "engine": "google_shopping",
                "google_domain": "google.com",
                "q": query,
                "num": min(12, num_products * 2),  # Request more than needed in case some are filtered out
                "api_key": self.api_key,
                "hl": "en",
                "gl": "us",
                "tbs": "mr:1",  # Include only relevant results
            }
            
            # Add price range if provided
            if min_price is not None and max_price is not None:
                params["tbs"] += f",price:1,ppr_min:{min_price},ppr_max:{max_price}"
            elif min_price is not None:
                params["tbs"] += f",price:1,ppr_min:{min_price}"
            elif max_price is not None:
                params["tbs"] += f",price:1,ppr_max:{max_price}"
            elif budget is not None:
                # Set max price to budget
                params["tbs"] += f",price:1,ppr_max:{budget}"
                
            logger.info(f"Searching products for query: {query}")
            
            # Get a connection from the pool manager instead of creating a new client
            pool = get_connection_pool()
            client = await pool.get_client("serpapi")
            
            # Perform the request using the pooled connection
            response = await client.get(self.search_url, params=params)
            
            # Handle rate limiting
            if response.status_code == 429:
                logger.warning("SerpAPI rate limit reached")
                self.rate_limited = True
                # Set reset time to 5 minutes from now
                self.rate_limit_reset = time.time() + 300
                return self._get_fallback_products(category or "Top", num_products)
                
            # Handle other errors
            if response.status_code != 200:
                logger.error(f"SerpAPI error: {response.status_code} - {response.text}")
                return self._get_fallback_products(category or "Top", num_products)
                
            # Parse the response data
            response_data = response.json()
            shopping_results = response_data.get("shopping_results", [])
            
            # Process the results
            products = []
            for item in shopping_results[:num_products]:
                price_raw = item.get("price", "")
                # Extract numeric price from string (e.g. "$49.99" -> 49.99)
                price_match = re.search(r'[\d,]+\.?\d*', price_raw.replace("$", ""))
                price = float(price_match.group().replace(",", "")) if price_match else 0.0
                
                thumbnail = item.get("thumbnail", "")
                # Get a higher-quality image if possible
                if "googleusercontent.com" in thumbnail:
                    image = self._get_high_quality_image(thumbnail)
                else:
                    image = thumbnail
                
                product = {
                    "product_id": f"serpapi-{uuid.uuid4()}",
                    "product_name": item.get("title", "").strip(),
                    "brand": item.get("source", "").strip(),
                    "category": category or "uncategorized",
                    "price": price,
                    "image_url": image,
                    "product_url": item.get("link", ""),
                    "currency": "USD",
                    "description": item.get("snippet", ""),
                    "source": "serpapi"
                }
                
                products.append(product)
            
            # Cache the results if we got any
            if products:
                cache_service.set(cache_key, products, "medium")
                return products
            else:
                logger.warning(f"No products found for query: {query}")
                return self._get_fallback_products(category or "Top", num_products)
                
        except asyncio.TimeoutError:
            logger.error(f"Timeout while searching products for query: {query}")
            return self._get_fallback_products(category or "Top", num_products)
        except Exception as e:
            logger.error(f"Error during product search for query '{query}': {str(e)}")
            return self._get_fallback_products(category or "Top", num_products)
        
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