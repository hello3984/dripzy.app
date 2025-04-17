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
import certifi

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
    
    def __init__(self, api_key=None):
        """Initialize the SerpAPI service with an API key."""
        self.api_key = api_key or settings.SERPAPI_API_KEY
        if not self.api_key:
            logger.warning("No SerpAPI key provided")
        else:
            logger.info("SerpAPI key loaded from settings.")
            
        # Set up SSL context with certificate verification
        self.ssl_context = self._create_ssl_context()
        
        # Initialize cache with configurable TTL
        self.short_cache_ttl = int(os.getenv("CACHE_TTL_SHORT", "300"))  # 5 minutes
        self.medium_cache_ttl = int(os.getenv("CACHE_TTL_MEDIUM", "3600"))  # 1 hour
        self.long_cache_ttl = int(os.getenv("CACHE_TTL_LONG", "86400"))  # 24 hours
        
        # URL for SerpAPI searches
        self.search_url = "https://serpapi.com/search"
        
        # Track rate limiting
        self.rate_limited = False
        self.rate_limit_reset = 0
        
    def _create_ssl_context(self):
        """Create a secure SSL context with proper certificate verification"""
        try:
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            logger.info("Created verified SSL context for SerpAPI service")
            return ssl_context
        except Exception as e:
            logger.error(f"Error creating SSL context: {str(e)}")
            # Fallback to default
            return ssl.create_default_context()
    
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
        category: str = None,
        num_results: int = 6
    ) -> List[Dict[str, Any]]:
        """
        Search for products using SerpAPI's Google Shopping search.
        
        Args:
            query: The search query for products
            category: Optional product category
            num_results: Number of results to return (default: 6)
            
        Returns:
            List of product dictionaries with details
        """
        if not self.api_key:
            logger.warning("Missing SerpAPI key, returning fallback products")
            return self._get_fallback_products(query, category)
        
        # Clean and prepare the query
        cleaned_query = query.strip()
        if category:
            # Add category as prefix if provided (helps narrow results)
            cleaned_query = f"{category} {cleaned_query}" if category else cleaned_query
        
        logger.info(f"Searching products for query: {cleaned_query}")
        
        # Build the request parameters
        params = {
            "api_key": self.api_key,
            "engine": "google_shopping",
            "google_domain": "google.com",
            "q": cleaned_query,
            "num": num_results * 2,  # Request more than needed to filter
            "hl": "en",
            "gl": "us",
            "tbs": "mr:1" # Sort by relevance
        }
        
        try:
            # Get connection pool
            pool = get_connection_pool("serpapi")
            
            # Make the request using the connection pool
            async with pool.acquire() as client:
                # Set the SSL context for this request
                client._transport = httpx.AsyncHTTPTransport(verify=certifi.where())
                
                response = await client.get("https://serpapi.com/search", params=params)
                response.raise_for_status()
                data = response.json()
                
                if "shopping_results" not in data:
                    logger.warning(f"No shopping results returned for query: {cleaned_query}")
                    return self._get_fallback_products(query, category)
                
                # Process and format the results
                return self._process_products(data["shopping_results"], num_results, category)
                
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            logger.error(f"HTTP error during product search for query '{query}': {status_code}")
            
            # Handle rate limiting
            if status_code == 429:
                logger.warning("SerpAPI rate limit reached, using fallback products")
            
            return self._get_fallback_products(query, category)
            
        except (httpx.RequestError, httpx.ConnectError, ssl.SSLError) as e:
            logger.error(f"Error during product search for query '{query}': {str(e)}")
            return self._get_fallback_products(query, category)
            
        except Exception as e:
            logger.error(f"Unexpected error during product search for query '{query}': {str(e)}")
            return self._get_fallback_products(query, category)
    
    def _process_products(
        self, 
        results: List[Dict[str, Any]], 
        limit: int,
        category: str = None
    ) -> List[Dict[str, Any]]:
        """Process and format the search results."""
        products = []
        
        # Take only the requested number of results
        results = results[:limit]
        
        for result in results:
            # Generate a unique product ID
            product_id = f"serpapi-{uuid.uuid4()}"
            
            # Extract price as a float
            price = self._extract_price(result.get("price", "0"))
            
            # Standardize product fields
            product = {
                "product_id": product_id,
                "product_name": result.get("title", "Product Name"),
                "brand": result.get("source", ""),
                "category": category or "General",
                "price": price,
                "image_url": result.get("thumbnail", ""),
                "product_url": result.get("link", ""),
                "currency": "USD",
                "description": result.get("snippet", ""),
                "source": "serpapi"
            }
            
            products.append(product)
        
        return products
    
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
serpapi_service = SerpAPIService(api_key=settings.SERPAPI_API_KEY) 