import requests
import logging
import os
import json
import re
import time
import random
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables directly
load_dotenv()

logger = logging.getLogger(__name__)

# Increase cache TTL to reduce API calls
_cache = {}
_cache_timestamps = {}
_CACHE_TTL = 86400  # Cache expiration in seconds (24 hours instead of 1 hour)

# Track API status to avoid multiple failed calls
_api_status = {
    "last_checked": 0,
    "is_rate_limited": False,
    "reset_after": 0  # Time when we should try API again
}

class SerpApiService:
    """Service to interact with SerpAPI for product search"""
    
    def __init__(self):
        """Initialize the SerpAPI service with API key from environment variables"""
        # Get API key directly from environment, don't use settings
        self.api_key = os.getenv("SERPAPI_KEY")
        
        # Try reading from secret file if environment variable is not found
        if not self.api_key and os.path.exists("/etc/secrets/SERPAPI_KEY"):
            try:
                with open("/etc/secrets/SERPAPI_KEY", "r") as f:
                    self.api_key = f.read().strip()
                logger.info("Successfully loaded SERPAPI_KEY from secret file")
            except Exception as e:
                logger.error(f"Error reading secret file: {e}")
        
        if not self.api_key:
            logger.warning("SERPAPI_KEY not found in environment variables or secret files")
        else:
            masked_key = self.api_key[:4] + "..." + self.api_key[-4:] if len(self.api_key) > 8 else "***"
            logger.info(f"SERPAPI_KEY found (masked: {masked_key})")
            
        self.base_url = "https://serpapi.com/search"
        
    def search_products(self, 
                       query: str, 
                       category: str,
                       gender: str = "unisex",
                       min_price: Optional[float] = None,
                       max_price: Optional[float] = None,
                       limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for products using SerpAPI
        
        Args:
            query: Search query text
            category: Product category (Top, Bottom, Dress, etc.)
            gender: Gender filter (unisex, women, men)
            min_price: Minimum price filter
            max_price: Maximum price filter
            limit: Maximum number of results to return
            
        Returns:
            List of product dictionaries
        """
        try:
            if not self.api_key:
                logger.error("No SERPAPI_KEY available, cannot perform search")
                return self._get_fallback_products(category, query, limit, reason="No API key")
            
            # If we know the API is rate limited, don't even try the search
            current_time = time.time()
            if _api_status["is_rate_limited"] and current_time < _api_status["reset_after"]:
                logger.info("Skipping SerpAPI search - known rate limit")
                return self._get_fallback_products(category, query, limit, reason="Rate limit known")
            
            # Create search query with category and gender
            if gender.lower() in ["female", "women", "woman", "ladies"]:
                gender_term = "women's"
            elif gender.lower() in ["male", "men", "man"]:
                gender_term = "men's"
            else:
                gender_term = ""
                
            search_query = f"{gender_term} {category} {query}"
            
            # Check cache before making a request
            cache_key = f"{search_query}_{min_price}_{max_price}_{limit}"
            cached_result = self._get_from_cache(cache_key)
            if cached_result is not None:
                return cached_result
            
            logger.info(f"Searching SerpAPI for: {search_query}")
            
            # Make API request with improved error handling
            try:
                params = {
                    "api_key": self.api_key,
                    "engine": "google_shopping",
                    "q": search_query,
                    "num": min(limit * 2, 20),  # Request more results than needed
                    "google_domain": "google.com",
                    "gl": "us",  # Set location to US
                    "hl": "en",  # Set language to English
                    "tbm": "shop"  # Use shopping results
                }
                
                # Add price filters if provided
                if min_price:
                    params["price_min"] = min_price
                if max_price:
                    params["price_max"] = max_price
                
                response = requests.get(self.base_url, params=params, timeout=10)
                
                # Explicitly handle rate limiting
                if response.status_code == 429:
                    logger.warning("SerpAPI rate limit exceeded (429 response)")
                    _api_status["is_rate_limited"] = True
                    _api_status["reset_after"] = current_time + 3600  # Try again in 1 hour
                    return self._get_fallback_products(category, query, limit, reason="Rate limit exceeded (429)")
                    
                response.raise_for_status()
                
            except requests.exceptions.RequestException as req_error:
                # Check if this is a rate limit error
                if "429" in str(req_error):
                    logger.warning(f"SerpAPI rate limit error: {req_error}")
                    _api_status["is_rate_limited"] = True
                    _api_status["reset_after"] = current_time + 3600  # Try again in 1 hour
                    return self._get_fallback_products(category, query, limit, reason="Rate limit error")
                else:
                    logger.error(f"Request error: {req_error}")
                    return self._get_fallback_products(category, query, limit, reason=f"Request error: {str(req_error)}")
            
            # Reset rate limiting on successful response
            _api_status["is_rate_limited"] = False
            data = response.json()
            
            # Extract shopping results - check both formats
            shopping_results = data.get("shopping_results", [])
            if not shopping_results and "inline_shopping_results" in data:
                shopping_results = data.get("inline_shopping_results", [])
            
            if not shopping_results:
                logger.warning(f"No shopping results found for query: {search_query}")
                return self._get_fallback_products(category, query, limit, reason="No results found")
            
            # Process results
            products = []
            for i, item in enumerate(shopping_results[:limit*2]):
                price = self._extract_price(item)
                
                # Get source as brand
                brand = item.get("source", "")
                
                # Get thumbnail
                image_url = item.get("thumbnail", "")
                
                # Create product entry
                product = {
                    "product_id": f"serpapi-{i}",
                    "title": item.get("title", "Unknown Product"),
                    "description": item.get("snippet", "") or item.get("title", ""),
                    "category": category,
                    "price": price,
                    "brand": brand,
                    "image_url": image_url,
                    "thumbnail": image_url,
                    "link": item.get("link", "")
                }
                
                products.append(product)
                
                # Stop when we have enough products
                if len(products) >= limit:
                    break
            
            # Cache results for future use
            self._add_to_cache(cache_key, products)
            
            return products[:limit]
            
        except Exception as e:
            logger.error(f"Error searching products with SerpAPI: {e}")
            return self._get_fallback_products(category, query, limit, reason=f"Error: {str(e)}")
            
    def _add_to_cache(self, key: str, value: Any) -> None:
        """Add a value to the cache with current timestamp."""
        _cache[key] = value
        _cache_timestamps[key] = time.time()

    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get a value from cache if it exists and hasn't expired."""
        if key in _cache and key in _cache_timestamps:
            if time.time() - _cache_timestamps[key] < _CACHE_TTL:
                logger.info(f"Using cached result for {key}")
                return _cache[key]
            else:
                # Clear expired cache entry
                del _cache[key]
                del _cache_timestamps[key]
        return None
    
    def _extract_price(self, item: Dict) -> float:
        """Extract price from an item."""
        try:
            price_str = item.get("price", "")
            if not price_str:
                return 0.0
                
            # Clean up the price string
            if isinstance(price_str, str):
                # Remove currency symbols and commas
                price_str = re.sub(r'[^\d.]', '', price_str)
                return float(price_str) if price_str else 0.0
            elif isinstance(price_str, (int, float)):
                return float(price_str)
                
            return 0.0
        except Exception as e:
            logger.error(f"Error extracting price: {e}")
            return 0.0
            
    def _get_fallback_products(self, category: str, query: str, limit: int = 5, reason: str = "Unknown") -> List[Dict[str, Any]]:
        """Generate fallback products when real ones can't be fetched."""
        logger.warning(f"Using fallback products for {category}: {query} (Reason: {reason})")
        
        # Define fallback brands by category
        brands = {
            "Top": ["H&M", "Zara", "Uniqlo", "Gap", "J.Crew"],
            "Bottom": ["Levi's", "H&M", "American Eagle", "Gap", "Uniqlo"],
            "Dress": ["Zara", "H&M", "Mango", "ASOS", "Forever 21"],
            "Shoes": ["Nike", "Adidas", "Vans", "Converse", "New Balance"],
            "Accessory": ["Fossil", "Mango", "Zara", "H&M", "ASOS"],
            "Outerwear": ["North Face", "Columbia", "Patagonia", "Uniqlo", "Gap"],
        }
        
        # Select a brand based on category
        category_key = next((k for k in brands.keys() if k.lower() in category.lower()), "Top")
        
        # Default fallback image URLs by category
        default_images = {
            "Top": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=600",
            "Bottom": "https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?w=600",
            "Dress": "https://images.unsplash.com/photo-1496747611176-843222e1e57c?w=600",
            "Shoes": "https://images.unsplash.com/photo-1560343090-f0409e92791a?w=600",
            "Accessory": "https://images.unsplash.com/photo-1608042314453-ae338d80c427?w=600",
            "Outerwear": "https://images.unsplash.com/photo-1539533113208-f6df8cc8b543?w=600",
        }
        
        # Get appropriate image URL
        image_key = next((k for k in default_images.keys() if k.lower() in category.lower()), "Top")
        image_url = default_images.get(image_key)
        
        # Create fallback products
        products = []
        for i in range(limit):
            brand = brands[category_key][i % len(brands[category_key])]
            price = round(19.99 + (i * 10), 2)  # Vary prices
            
            product = {
                "product_id": f"fallback-{category}-{i}",
                "title": f"{brand} {category} Item {i+1}",
                "description": f"Fallback {category} product (API call failed: {reason})",
                "category": category,
                "price": price,
                "brand": brand,
                "image_url": image_url,
                "thumbnail": image_url,
                "link": "",
                "fallback": True,
                "fallback_reason": reason
            }
            
            products.append(product)
            
        return products

# Create a singleton instance
serpapi_service = SerpApiService() 