import requests
import logging
import os
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class SkimlinksService:
    """Service to interact with Skimlinks API for product search and affiliate links"""

    def __init__(self):
        # Your Skimlinks API credentials - set these in your environment variables
        self.account_id = os.getenv("SKIMLINKS_ACCOUNT_ID", "282510")
        self.api_key = os.getenv("SKIMLINKS_API_KEY", "")  # Set this in your environment variables
        self.base_url = "https://api.skimapis.com/v3"
    
    def search_products(self, query: str, category: Optional[str] = None, 
                        limit: int = 5, min_price: Optional[float] = None, 
                        max_price: Optional[float] = None) -> List[Dict[Any, Any]]:
        """
        Search for products using Skimlinks Product API
        
        Args:
            query: Search query for products
            category: Optional category to filter by
            limit: Maximum number of products to return
            min_price: Minimum price filter
            max_price: Maximum price filter
            
        Returns:
            List of product dictionaries
        """
        try:
            endpoint = f"{self.base_url}/products"
            
            # Build query parameters
            params = {
                "q": query,
                "limit": limit,
                "apikey": self.api_key
            }
            
            # Add optional filters
            if category:
                params["category"] = self._map_category(category)
                
            if min_price:
                params["price_min"] = min_price
                
            if max_price:
                params["price_max"] = max_price
            
            # Make API request
            logger.info(f"Searching Skimlinks for: {query}")
            response = requests.get(endpoint, params=params)
            
            # Check for successful response
            if response.status_code == 200:
                data = response.json()
                products = data.get("products", [])
                logger.info(f"Found {len(products)} products via Skimlinks")
                
                # Transform products to match your existing format
                transformed_products = self._transform_products(products, category)
                return transformed_products
            else:
                logger.warning(f"Skimlinks API error: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error searching Skimlinks products: {str(e)}")
            return []
    
    def _transform_products(self, products: List[Dict], category: Optional[str] = None) -> List[Dict]:
        """Transform Skimlinks products to match your app's format"""
        transformed = []
        
        for product in products:
            # Extract relevant fields from Skimlinks response
            transformed_product = {
                "product_id": product.get("id", ""),
                "product_name": product.get("name", ""),
                "brand": product.get("brand", {}).get("name", "Various"),
                "category": category or self._detect_category(product),
                "price": float(product.get("price", {}).get("amount", 0)),
                "image_url": product.get("image_url", ""),
                "description": product.get("description", ""),
                "source": product.get("merchant", {}).get("name", ""),
                "product_url": self._get_affiliate_url(product.get("url", "")),
                "currency": product.get("price", {}).get("currency", "USD")
            }
            transformed.append(transformed_product)
            
        return transformed
    
    def _get_affiliate_url(self, original_url: str) -> str:
        """Convert a product URL to an affiliate URL using Skimlinks"""
        # For basic implementation, just append the account ID to be picked up by the Skimlinks script
        # The Skimlinks script you added to your frontend will automatically convert these
        if "?" in original_url:
            return f"{original_url}&skimlinks_account={self.account_id}"
        else:
            return f"{original_url}?skimlinks_account={self.account_id}"
    
    def _map_category(self, app_category: str) -> str:
        """Map your app's categories to Skimlinks categories"""
        category_map = {
            "Top": "apparel",
            "Bottom": "apparel",
            "Shoes": "shoes",
            "Accessory": "accessories",
            "Dress": "apparel",
            "Outerwear": "apparel"
        }
        return category_map.get(app_category, "apparel")
    
    def _detect_category(self, product: Dict) -> str:
        """Detect product category from Skimlinks data"""
        # Extract and map Skimlinks category to your app's categories
        skim_category = product.get("category", {}).get("name", "").lower()
        
        if any(keyword in skim_category for keyword in ["shoes", "boots", "sneakers", "footwear"]):
            return "Shoes"
        elif any(keyword in skim_category for keyword in ["accessories", "jewelry", "watches", "bags"]):
            return "Accessory"
        elif any(keyword in skim_category for keyword in ["pants", "jeans", "shorts", "skirts"]):
            return "Bottom"
        elif any(keyword in skim_category for keyword in ["jackets", "coats", "outerwear"]):
            return "Outerwear"
        elif any(keyword in skim_category for keyword in ["dresses", "gowns"]):
            return "Dress"
        else:
            return "Top"  # Default to top

# Singleton instance
skimlinks_service = SkimlinksService() 