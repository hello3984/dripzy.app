import requests
import logging
import os
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class SerpApiService:
    """Service to interact with SerpAPI for product search"""
    
    def __init__(self):
        self.api_key = os.getenv("SERPAPI_KEY")
        if not self.api_key:
            logger.warning("SERPAPI_KEY not found in environment variables")
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
                return self._get_fallback_products(category, query, limit)
            
            # Create search query with category and gender
            if gender.lower() in ["female", "women", "woman", "ladies"]:
                gender_term = "women's"
            elif gender.lower() in ["male", "men", "man"]:
                gender_term = "men's"
            else:
                gender_term = ""
                
            search_query = f"{gender_term} {category} {query}"
            logger.info(f"Searching SerpAPI for: {search_query}")
            
            # Build parameters
            params = {
                "api_key": self.api_key,
                "engine": "google_shopping",
                "q": search_query,
                "num": limit * 2  # Request more results to account for filtering
            }
            
            # Add price filters if provided
            if min_price:
                params["price_min"] = min_price
            if max_price:
                params["price_max"] = max_price
                
            # Make API request
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract shopping results
            shopping_results = data.get("shopping_results", [])
            
            if not shopping_results:
                logger.warning(f"No shopping results found for query: {search_query}")
                return self._get_fallback_products(category, query, limit)
            
            # Transform to our format
            products = []
            for i, item in enumerate(shopping_results[:limit*2]):
                # Extract price - handle different formats
                price_str = item.get("price", "0")
                if isinstance(price_str, str):
                    # Remove currency symbol and commas
                    price_str = price_str.replace("$", "").replace(",", "")
                    # Try to extract just the number
                    import re
                    price_match = re.search(r'([\d.]+)', price_str)
                    if price_match:
                        price_str = price_match.group(1)
                
                try:
                    price = float(price_str)
                except (ValueError, TypeError):
                    price = 0.0
                
                product = {
                    "product_id": f"serpapi-{item.get('position', i)}",
                    "product_name": item.get("title", "Unknown Product"),
                    "brand": item.get("source", "Unknown Brand"),
                    "category": category,
                    "price": price,
                    "image_url": item.get("thumbnail", ""),
                    "description": item.get("snippet", ""),
                    "source": "SerpAPI",
                    "product_url": item.get("link", "#")
                }
                products.append(product)
            
            # Filter out products with missing images
            products = [p for p in products if p["image_url"]]
            
            # Return limited number of products
            return products[:limit]
            
        except Exception as e:
            logger.error(f"Error searching products with SerpAPI: {e}")
            return self._get_fallback_products(category, query, limit)
    
    def _get_fallback_products(self, category: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Generate fallback products when API fails"""
        logger.warning(f"Using fallback products for {category}: {query}")
        
        # Extract color from query
        colors = ["black", "white", "blue", "red", "green", "yellow", "purple", 
                 "pink", "brown", "gray", "beige", "navy"]
        
        color = next((c for c in colors if c in query.lower()), "blue")
        
        products = []
        for i in range(limit):
            if category == "Top":
                name = f"{color.capitalize()} T-Shirt"
                img = "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=800"
                price = 29.99 + (i * 5)
            elif category == "Bottom":
                name = f"{color.capitalize()} Jeans"
                img = "https://images.unsplash.com/photo-1541099649105-f69ad21f3246?w=800"
                price = 49.99 + (i * 5)
            elif category == "Dress":
                name = f"{color.capitalize()} Casual Dress"
                img = "https://images.unsplash.com/photo-1612336307429-8a898d10e223?w=800"
                price = 59.99 + (i * 5)
            elif category == "Shoes":
                name = f"{color.capitalize()} Casual Shoes"
                img = "https://images.unsplash.com/photo-1560769629-975ec94e6a86?w=800"
                price = 79.99 + (i * 5)
            elif category == "Accessory":
                name = f"{color.capitalize()} Fashion Accessory"
                img = "https://images.unsplash.com/photo-1611652022419-a9419f74343d?w=800"
                price = 19.99 + (i * 2)
            else:
                name = f"{color.capitalize()} {category} Item"
                img = "https://images.unsplash.com/photo-1551488831-00ddcb6c6bd3?w=800"
                price = 39.99 + (i * 4)
            
            product = {
                "product_id": f"fallback-{category.lower()}-{i}",
                "product_name": name,
                "brand": "Fallback Brand",
                "category": category,
                "price": price,
                "image_url": img,
                "description": f"Fallback {category.lower()} product when API results are unavailable",
                "source": "Fallback",
                "product_url": "#"
            }
            products.append(product)
        
        return products

# Create an instance to export
serpapi_service = SerpApiService() 