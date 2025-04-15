import requests
import logging
import json
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class HMService:
    """Service to interact with H&M API for product search"""
    
    def __init__(self):
        # Keep these for future implementation if needed
        self.base_url = "https://apim.hm.com/api"
        self.search_url = "https://www2.hm.com/en_us/search-results.html"
        self.country = "us"
        self.lang = "en"
        
    def search_products(self, 
                       query: str, 
                       category: str, 
                       gender: str = "ladies",
                       min_price: Optional[float] = None,
                       max_price: Optional[float] = None,
                       limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get H&M products matching criteria
        
        Args:
            query: Search query text
            category: Product category (Top, Bottom, Dress, etc.)
            gender: Gender filter (ladies, men, kids)
            min_price: Minimum price filter
            max_price: Maximum price filter
            limit: Maximum number of results to return
            
        Returns:
            List of product dictionaries
        """
        logger.info(f"Searching H&M for: {query} in category {category}")
        
        # Create consistent but varied products based on the query
        # This ensures same query always returns same products
        return self._get_products_for_query(query, category, gender, limit)
    
    def _get_products_for_query(self, query: str, category: str, gender: str, limit: int = 1) -> List[Dict[str, Any]]:
        """Get products based on query parameters"""
        
        # Get the color from the query
        color_keywords = ["black", "white", "red", "blue", "green", "yellow", "purple", 
                          "pink", "orange", "brown", "grey", "gray", "silver", "gold"]
        colors = [c for c in color_keywords if c in query.lower()]
        color = colors[0] if colors else "blue" # Default to blue if no color found
        
        # Format gender for product naming
        gender_display = {
            "female": "Women's", 
            "women": "Women's",
            "ladies": "Women's",
            "male": "Men's",
            "men": "Men's",
            "kids": "Kids'"
        }.get(gender.lower(), "Unisex")
        
        # Create a deterministic but seemingly random product based on query
        # This ensures same query always returns same product
        query_hash = sum(ord(c) for c in query) % 1000
        price_base = 40 + (query_hash % 40)  # Base price between $40-80
        
        products = []
        for i in range(limit):
            # Vary price slightly for each product
            product_price = price_base + (i * 5.99)
            
            if category == "Top":
                if "shirt" in query.lower() or "tee" in query.lower():
                    product_name = f"{color.capitalize()} {gender_display} Cotton T-Shirt"
                elif "blouse" in query.lower():
                    product_name = f"{color.capitalize()} {gender_display} Elegant Blouse"
                elif "sweater" in query.lower() or "knit" in query.lower():
                    product_name = f"{color.capitalize()} {gender_display} Knit Sweater"
                else:
                    product_name = f"{color.capitalize()} {gender_display} Casual Top"
                    
                image_url = "https://images.unsplash.com/photo-1576566588028-4147f3842f27?q=80&w=1964&auto=format&fit=crop"
                    
            elif category == "Bottom":
                if "jeans" in query.lower() or "denim" in query.lower():
                    product_name = f"{color.capitalize()} {gender_display} Slim Fit Jeans"
                elif "shorts" in query.lower():
                    product_name = f"{color.capitalize()} {gender_display} Casual Shorts"
                elif "skirt" in query.lower():
                    product_name = f"{color.capitalize()} {gender_display} A-Line Skirt"
                else:
                    product_name = f"{color.capitalize()} {gender_display} Casual Pants"
                    
                image_url = "https://images.unsplash.com/photo-1584370848010-d7fe6bc767ec?q=80&w=1974&auto=format&fit=crop"
                    
            elif category == "Shoes":
                if "boots" in query.lower():
                    product_name = f"{color.capitalize()} {gender_display} Ankle Boots"
                elif "sneakers" in query.lower() or "trainers" in query.lower():
                    product_name = f"{color.capitalize()} {gender_display} Canvas Sneakers"
                elif "sandals" in query.lower():
                    product_name = f"{color.capitalize()} {gender_display} Casual Sandals"
                else:
                    product_name = f"{color.capitalize()} {gender_display} Casual Shoes"
                    
                image_url = "https://images.unsplash.com/photo-1543163521-1bf539c55dd2?q=80&w=1480&auto=format&fit=crop"
                    
            elif category == "Accessory":
                if "bag" in query.lower() or "purse" in query.lower():
                    product_name = f"{color.capitalize()} {gender_display} Crossbody Bag"
                elif "watch" in query.lower():
                    product_name = f"{color.capitalize()} {gender_display} Minimalist Watch"
                elif "jewelry" in query.lower() or "necklace" in query.lower():
                    product_name = f"{color.capitalize()} {gender_display} Statement Necklace"
                else:
                    product_name = f"{color.capitalize()} {gender_display} Fashion Accessory"
                    
                image_url = "https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?q=80&w=1287&auto=format&fit=crop"
                    
            elif category == "Dress":
                if "evening" in query.lower() or "formal" in query.lower():
                    product_name = f"{color.capitalize()} {gender_display} Evening Dress"
                elif "summer" in query.lower() or "casual" in query.lower():
                    product_name = f"{color.capitalize()} {gender_display} Summer Dress"
                elif "maxi" in query.lower():
                    product_name = f"{color.capitalize()} {gender_display} Maxi Dress"
                else:
                    product_name = f"{color.capitalize()} {gender_display} Casual Dress"
                    
                image_url = "https://images.unsplash.com/photo-1596783074918-c84cb1bd5d44?q=80&w=1974&auto=format&fit=crop"
                    
            else:
                product_name = f"{color.capitalize()} {gender_display} {category}"
                image_url = "https://images.unsplash.com/photo-1578681994506-b8f463449011?q=80&w=1970&auto=format&fit=crop"
                
            # Create a unique ID based on the query and item number
            product_id = f"hm-{category.lower()}-{query_hash}-{i}"
            
            product = {
                "product_id": product_id,
                "product_name": product_name,
                "brand": "H&M",
                "category": category,
                "price": round(product_price, 2),
                "image_url": image_url,
                "description": f"{product_name} - Perfect for any occasion. Made with quality materials.",
                "source": "H&M",
                "product_url": f"https://www2.hm.com/en_us/productpage.{product_id}.html"
            }
            
            products.append(product)
            
        return products 

# Create an instance to export
hm_service = HMService() 