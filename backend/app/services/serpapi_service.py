import requests
import logging
import os
import json
import re
import time
from typing import Dict, List, Optional, Any, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class SerpApiService:
    """Service to interact with SerpAPI for product search"""
    
    def __init__(self):
        # Add debug logging for environment variables
        logger.info("Initializing SerpAPI Service")
        logger.info(f"Environment variables keys: {', '.join([k for k in os.environ.keys() if not k.startswith('_')])}")
        
        # Try multiple ways to get the key
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
        
        # Initialize in-memory cache
        # Using format {cache_key: {"data": results, "timestamp": time.time()}}
        self.cache = {}
        self.cache_ttl = 3600  # Cache results for 1 hour
        
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
                return self._get_fallback_products(category, query, limit)
            
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
            if cached_result:
                logger.info(f"Using cached results for query: {search_query}")
                return cached_result
            
            logger.info(f"Searching SerpAPI for: {search_query}")
            
            # Enhanced parameters based on Gensmo's implementation
            params = {
                "api_key": self.api_key,
                "engine": "google_shopping",
                "q": search_query,
                "num": limit * 2,  # Request more results to account for filtering
                "google_domain": "google.com",
                "gl": "us",        # Set location to US for consistent results
                "hl": "en",        # Set language to English
                "tbm": "shop",     # Ensure we're using shopping results
                "tbs": "mr:1"      # Include "in stock" items
            }
            
            # Add price filters if provided
            if min_price:
                params["price_min"] = min_price
            if max_price:
                params["price_max"] = max_price
                
            # Add quality filters based on category
            if category.lower() in ["shoes", "footwear"]:
                params["tbs"] += ",avg_rating:4"  # Higher rating threshold for shoes
            
            # Make API request
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract shopping results - try both formats for compatibility
            shopping_results = data.get("shopping_results", [])
            if not shopping_results and "inline_shopping_results" in data:
                shopping_results = data.get("inline_shopping_results", [])
            
            if not shopping_results:
                logger.warning(f"No shopping results found for query: {search_query}")
                return self._get_fallback_products(category, query, limit)
            
            # Transform to our format with enhanced data extraction
            products = self._process_shopping_results(shopping_results, category, limit)
            
            # Cache the results
            self._add_to_cache(cache_key, products)
            
            return products[:limit]
            
        except Exception as e:
            logger.error(f"Error searching products with SerpAPI: {e}")
            return self._get_fallback_products(category, query, limit)
    
    def _process_shopping_results(self, shopping_results: List[Dict], category: str, limit: int) -> List[Dict[str, Any]]:
        """Process and transform shopping results into our product format"""
        products = []
        
        for i, item in enumerate(shopping_results[:limit*2]):
            # Extract price with improved parsing
            price = self._extract_price(item)
            
            # Extract brand from source or title
            brand = item.get("source", "")
            if not brand and "title" in item:
                # Try to extract brand from title (first word often)
                title_parts = item.get("title", "").split()
                if title_parts:
                    brand = title_parts[0]
            
            # Use direct thumbnail URL as Gensmo does
            image_url = item.get("thumbnail", "")
            
            # Get more detailed product info
            product = {
                "product_id": item.get("product_id", f"serpapi-{item.get('position', i)}"),
                "product_name": item.get("title", "Unknown Product"),
                "brand": brand,
                "category": category,
                "price": price,
                "formatted_price": item.get("price", f"${price:.2f}"),
                "image_url": image_url,
                "description": item.get("snippet", ""),
                "source": item.get("source", "SerpAPI"),
                "source_icon": item.get("source_icon", ""),
                "product_url": item.get("link", "#"),
                "rating": item.get("rating", 0),
                "reviews": item.get("reviews", 0),
                "search_id": self._extract_search_id(image_url)
            }
            
            # Add platform information (Amazon, etc.)
            extensions = item.get("extensions", [])
            if extensions:
                for ext in extensions:
                    if "amazon" in ext.lower():
                        product["platform"] = "amazon"
                        break
                else:
                    product["platform"] = "other"
                    
            products.append(product)
        
        # Filter out products with missing images and sort by relevance
        products = [p for p in products if p["image_url"]]
        
        # Sort products by combination of price and rating
        products.sort(key=lambda x: (x.get("rating", 0) * 0.7 + 100.0/(x.get("price", 100) + 1) * 0.3), reverse=True)
        
        return products[:limit]
    
    def _extract_price(self, item: Dict) -> float:
        """Extract price from SerpAPI item with improved parsing"""
        # First try the extracted_price field directly
        if "extracted_price" in item:
            try:
                return float(item["extracted_price"])
            except (ValueError, TypeError):
                pass
        
        # Then try parsing from the price string
        price_str = item.get("price", "0")
        if isinstance(price_str, str):
            # Remove currency symbol, commas, and other characters
            price_str = re.sub(r'[^\d.]', '', price_str.replace(",", ""))
            # Find the first valid number
            price_match = re.search(r'([\d.]+)', price_str)
            if price_match:
                try:
                    return float(price_match.group(1))
                except (ValueError, TypeError):
                    pass
        
        return 0.0
    
    def _extract_search_id(self, url: str) -> Optional[str]:
        """Extract the SerpAPI search ID from a thumbnail URL"""
        if not url:
            return None
            
        # Pattern: serpapi.com/searches/[SEARCH_ID]/images/
        match = re.search(r'searches/([^/]+)/images/', url)
        if match:
            return match.group(1)
        return None
    
    def _get_from_cache(self, cache_key: str) -> Optional[List[Dict]]:
        """Get results from cache if available and not expired"""
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            # Check if cache is still valid
            if time.time() - cache_entry["timestamp"] < self.cache_ttl:
                return cache_entry["data"]
            else:
                # Remove expired cache
                del self.cache[cache_key]
        return None
    
    def _add_to_cache(self, cache_key: str, data: List[Dict]):
        """Add results to cache with timestamp"""
        self.cache[cache_key] = {
            "data": data,
            "timestamp": time.time()
        }
    
    def _get_fallback_products(self, category: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Generate fallback products when API fails"""
        logger.warning(f"Using fallback products for {category}: {query}")
        
        # Extract color from query
        colors = ["black", "white", "blue", "red", "green", "yellow", "purple", 
                 "pink", "brown", "gray", "beige", "navy"]
        
        color = next((c for c in colors if c in query.lower()), "blue")
        
        # More realistic product data for fallbacks
        fallback_data = {
            "Top": [
                {"name": f"Light blue denim chambray shirt", "brand": "H&M", "price": 29.99, 
                 "img": "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=800"},
                {"name": f"{color.capitalize()} cotton t-shirt", "brand": "Gap", "price": 24.99, 
                 "img": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=800"},
                {"name": f"{color.capitalize()} linen button-up", "brand": "Zara", "price": 39.99, 
                 "img": "https://images.unsplash.com/photo-1589310243389-96a5483213a8?w=800"},
            ],
            "Bottom": [
                {"name": f"Khaki cotton twill pants", "brand": "Dockers", "price": 49.99, 
                 "img": "https://images.unsplash.com/photo-1473966968600-fa801b869a1a?w=800"},
                {"name": f"Medium wash straight-leg jeans", "brand": "Lee", "price": 54.99, 
                 "img": "https://images.unsplash.com/photo-1541099649105-f69ad21f3246?w=800"},
                {"name": f"{color.capitalize()} high-rise leggings", "brand": "Athleta", "price": 59.99, 
                 "img": "https://images.unsplash.com/photo-1556386734-7fad9342a257?w=800"},
            ],
            "Dress": [
                {"name": f"{color.capitalize()} wrap midi dress", "brand": "Lulus", "price": 59.99, 
                 "img": "https://images.unsplash.com/photo-1612336307429-8a898d10e223?w=800"},
                {"name": f"Floral patterned maxi dress", "brand": "Reformation", "price": 89.99, 
                 "img": "https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=800"},
                {"name": f"Black sleeveless sheath dress", "brand": "Express", "price": 69.99, 
                 "img": "https://images.unsplash.com/photo-1539008835657-9e8e9680c956?w=800"},
            ],
            "Shoes": [
                {"name": f"Low-top canvas sneakers", "brand": "FRACORA", "price": 79.99, 
                 "img": "https://images.unsplash.com/photo-1560769629-975ec94e6a86?w=800"},
                {"name": f"{color.capitalize()} leather ankle boots", "brand": "Steve Madden", "price": 99.99, 
                 "img": "https://images.unsplash.com/photo-1542838132-92c53300491e?w=800"},
                {"name": f"Open-toe block heel sandals", "brand": "Sam Edelman", "price": 69.99, 
                 "img": "https://images.unsplash.com/photo-1543163521-1bf539c55dd2?w=800"},
            ],
            "Accessory": [
                {"name": f"{color.capitalize()} leather crossbody bag", "brand": "Coach", "price": 149.99, 
                 "img": "https://images.unsplash.com/photo-1584917865442-de89df76afd3?w=800"},
                {"name": f"Gold-plated layered necklace", "brand": "Madewell", "price": 39.99, 
                 "img": "https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?w=800"},
                {"name": f"Oversized square sunglasses", "brand": "Ray-Ban", "price": 129.99, 
                 "img": "https://images.unsplash.com/photo-1577803645773-f96470509666?w=800"},
            ]
        }
        
        # Default category if not found
        if category not in fallback_data:
            fallback_data[category] = [
                {"name": f"{color.capitalize()} {category}", "brand": "Fashion Brand", "price": 39.99, 
                 "img": "https://images.unsplash.com/photo-1551488831-00ddcb6c6bd3?w=800"}
            ]
        
        products = []
        items = fallback_data.get(category, fallback_data["Top"])
        
        for i in range(min(limit, len(items) * 2)):
            # Cycle through the available items if needed
            item = items[i % len(items)]
            
            product = {
                "product_id": f"fallback-{category.lower()}-{i}",
                "product_name": item["name"],
                "brand": item["brand"],
                "category": category,
                "price": item["price"] + (i * 3),
                "formatted_price": f"${item['price'] + (i * 3):.2f}",
                "image_url": item["img"],
                "description": f"Quality {category.lower()} from {item['brand']}",
                "source": "Fallback",
                "product_url": "#",
                "rating": 4.0 + (i % 10) / 10,
                "reviews": 10 + (i * 7),
            }
            products.append(product)
        
        return products[:limit]

# Create an instance to export
serpapi_service = SerpApiService() 