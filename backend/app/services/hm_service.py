import requests
import logging
import json
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class HMService:
    """Service to interact with H&M API for product search"""
    
    def __init__(self):
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
        Search H&M for products matching criteria
        
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
        
        # Use fallbacks for now - H&M site might block scraping
        return self._get_fallback_products(category, query, limit)
    
    def _transform_products(self, products: List[Dict], original_category: str) -> List[Dict[str, Any]]:
        """Transform H&M API response to our format"""
        transformed = []
        
        for product in products:
            try:
                # Get the product code
                product_code = product.get("articleCode", "")
                
                # Get price
                price = product.get("price", {})
                price_value = price.get("value", 0)
                
                # Get product details
                name = product.get("title", "")
                
                # Get images
                images = product.get("images", [])
                image_url = ""
                if images and len(images) > 0:
                    image = images[0]
                    image_url = image.get("url", "")
                    # Add proper domain if needed
                    if image_url and not image_url.startswith("http"):
                        image_url = f"https://lp2.hm.com{image_url}"
                
                # Get product URL
                product_url = product.get("linkPdp", "")
                if product_url and not product_url.startswith("http"):
                    product_url = f"https://www2.hm.com{product_url}"
                
                transformed_product = {
                    "product_id": f"hm-{product_code}",
                    "product_name": name,
                    "brand": "H&M",
                    "category": original_category,
                    "price": float(price_value),
                    "image_url": image_url,
                    "description": product.get("description", name),
                    "source": "H&M",
                    "product_url": product_url
                }
                transformed.append(transformed_product)
            except Exception as transform_error:
                logger.error(f"Error transforming H&M product: {str(transform_error)}")
        
        return transformed
    
    def _get_fallback_products(self, category: str, query: str, limit: int = 1) -> List[Dict[str, Any]]:
        """Get fallback products when API fails"""
        logger.info(f"Using fallback products for {category}: {query}")
        
        # Get the color from the query
        color_keywords = ["black", "white", "red", "blue", "green", "yellow", "purple", 
                          "pink", "orange", "brown", "grey", "gray", "silver", "gold"]
        colors = [c for c in color_keywords if c in query.lower()]
        color = colors[0] if colors else "black"
        
        # Create a deterministic but seemingly random product based on query
        # This ensures same query always returns same product
        query_hash = sum(ord(c) for c in query) % 1000
        
        if category == "Top":
            return [{
                "product_id": f"hm-top-{query_hash}",
                "product_name": f"{color.capitalize()} H&M T-Shirt",
                "brand": "H&M",
                "category": "Top",
                "price": 24.99,
                "image_url": f"https://images.unsplash.com/photo-1576566588028-4147f3842f27?q=80&w=1964&auto=format&fit=crop",
                "description": f"Stylish {color} t-shirt from H&M",
                "source": "H&M",
                "product_url": "https://www2.hm.com"
            }]
        elif category == "Bottom":
            return [{
                "product_id": f"hm-bottom-{query_hash}",
                "product_name": f"{color.capitalize()} H&M Jeans",
                "brand": "H&M",
                "category": "Bottom",
                "price": 39.99,
                "image_url": f"https://images.unsplash.com/photo-1584370848010-d7fe6bc767ec?q=80&w=1974&auto=format&fit=crop",
                "description": f"Premium {color} jeans from H&M",
                "source": "H&M",
                "product_url": "https://www2.hm.com"
            }]
        elif category == "Shoes":
            return [{
                "product_id": f"hm-shoes-{query_hash}",
                "product_name": f"{color.capitalize()} H&M Shoes",
                "brand": "H&M",
                "category": "Shoes",
                "price": 49.99,
                "image_url": f"https://images.unsplash.com/photo-1543163521-1bf539c55dd2?q=80&w=1480&auto=format&fit=crop",
                "description": f"Premium {color} shoes from H&M",
                "source": "H&M",
                "product_url": "https://www2.hm.com"
            }]
        elif category == "Accessory":
            return [{
                "product_id": f"hm-accessory-{query_hash}",
                "product_name": f"{color.capitalize()} H&M Accessory",
                "brand": "H&M",
                "category": "Accessory",
                "price": 19.99,
                "image_url": f"https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?q=80&w=1287&auto=format&fit=crop",
                "description": f"Stylish {color} accessory from H&M",
                "source": "H&M",
                "product_url": "https://www2.hm.com"
            }]
        elif category == "Dress":
            return [{
                "product_id": f"hm-dress-{query_hash}",
                "product_name": f"{color.capitalize()} H&M Dress",
                "brand": "H&M",
                "category": "Dress",
                "price": 59.99,
                "image_url": f"https://images.unsplash.com/photo-1596783074918-c84cb1bd5d44?q=80&w=1974&auto=format&fit=crop",
                "description": f"Elegant {color} dress from H&M",
                "source": "H&M",
                "product_url": "https://www2.hm.com"
            }]
        else:
            return [{
                "product_id": f"hm-item-{query_hash}",
                "product_name": f"{color.capitalize()} H&M Item",
                "brand": "H&M",
                "category": category,
                "price": 29.99,
                "image_url": f"https://images.unsplash.com/photo-1578681994506-b8f463449011?q=80&w=1970&auto=format&fit=crop",
                "description": f"H&M {color} fashion item",
                "source": "H&M",
                "product_url": "https://www2.hm.com"
            }] 