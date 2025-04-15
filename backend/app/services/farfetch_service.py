import requests
import logging
import os
from typing import Dict, List, Optional, Any
import random
import json

logger = logging.getLogger(__name__)

class FarfetchService:
    """Service to interact with Farfetch API for product search"""
    
    def __init__(self):
        # Farfetch API credentials - set these in your environment variables
        self.client_id = os.getenv("FARFETCH_CLIENT_ID", "")
        self.client_secret = os.getenv("FARFETCH_CLIENT_SECRET", "")
        self.base_url = "https://publicapi.farfetch.com/v1"
        self.auth_url = "https://publicapi.farfetch.com/authentication"
        self.token = None
        self.country = "US"
        self.currency = "USD"
        
    def get_token(self) -> str:
        """Get authentication token from Farfetch API"""
        if self.token:
            return self.token
            
        try:
            if not self.client_id or not self.client_secret:
                logger.warning("Farfetch credentials not configured. Using mock data.")
                return ""
                
            response = requests.post(
                self.auth_url,
                data={
                    "grant_type": "client_credentials",
                    "scope": "api",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                token_type = data.get("token_type")
                access_token = data.get("access_token")
                self.token = f"{token_type} {access_token}"
                return self.token
            else:
                logger.error(f"Failed to get Farfetch token: {response.status_code} - {response.text}")
                return ""
                
        except Exception as e:
            logger.error(f"Error getting Farfetch token: {str(e)}")
            return ""
    
    def search_products(self, 
                       query: str, 
                       category: str, 
                       gender: str = "female",
                       min_price: Optional[float] = None,
                       max_price: Optional[float] = None,
                       limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search Farfetch for products matching criteria
        
        Args:
            query: Search query text
            category: Product category (Top, Bottom, Dress, etc.)
            gender: Gender filter (female, male, unisex)
            min_price: Minimum price filter
            max_price: Maximum price filter
            limit: Maximum number of results to return
            
        Returns:
            List of product dictionaries in our app's format
        """
        logger.info(f"Searching Farfetch for: {query} in category {category}")
        
        # Map our categories to Farfetch categories
        category_map = {
            "Top": "clothing",
            "Bottom": "clothing", 
            "Dress": "clothing",
            "Shoes": "shoes",
            "Accessory": "accessories",
            "Outerwear": "clothing"
        }
        
        ff_category = category_map.get(category, "clothing")
        
        # Build query params
        params = {
            "searchText": query,
            "pageIndex": 0,
            "pageSize": limit,
            "sort": "default",
            "categories": ff_category,
            "gender": gender.lower()
        }
        
        if min_price:
            params["price"] = f"{min_price}-"
        if max_price:
            params["price"] = f"{params.get('price', '')}{max_price}"
            
        try:
            # If we don't have credentials, use fallback products
            if not self.client_id or not self.client_secret:
                logger.info("No Farfetch credentials, using fallback products")
                return self._get_fallback_products(category, query, limit)
                
            token = self.get_token()
            if not token:
                logger.warning("No valid Farfetch token, using fallback products")
                return self._get_fallback_products(category, query, limit)
                
            # Make API request
            headers = {
                "Authorization": token,
                "FF-Country": self.country,
                "FF-Currency": self.currency,
                "Content-Type": "application/json"
            }
            
            endpoint = f"{self.base_url}/listing"
            response = requests.get(endpoint, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                products = data.get("products", {}).get("entries", [])
                
                # Transform to our format
                transformed_products = self._transform_products(products, category)
                logger.info(f"Found {len(transformed_products)} products on Farfetch for: {query}")
                
                return transformed_products
            else:
                logger.warning(f"Farfetch API error: {response.status_code} - {response.text}")
                return self._get_fallback_products(category, query, limit)
                
        except Exception as e:
            logger.error(f"Error searching Farfetch: {str(e)}")
            return self._get_fallback_products(category, query, limit)
    
    def _transform_products(self, products: List[Dict], original_category: str) -> List[Dict[str, Any]]:
        """Transform Farfetch API response to our format"""
        transformed = []
        
        for product in products:
            # Handle category refinement
            if original_category == "Top":
                subcategory = self._detect_top_type(product)
            elif original_category == "Bottom":
                subcategory = self._detect_bottom_type(product)
            else:
                subcategory = original_category
            
            # Extract price data
            price_data = product.get("price", {})
            price = price_data.get("priceInclTaxes", 0)
            formatted_price = price_data.get("formattedPrice", "$0")
            
            # Extract image data
            images = product.get("images", [])
            image_url = images[0].get("url") if images else ""
            
            transformed_product = {
                "product_id": str(product.get("id", "")),
                "product_name": product.get("shortDescription", ""),
                "brand": product.get("brand", {}).get("name", "Farfetch"),
                "category": subcategory,
                "price": float(price),
                "image_url": image_url,
                "description": product.get("shortDescription", ""),
                "source": "Farfetch",
                "product_url": f"https://www.farfetch.com/shopping/item-{product.get('id', '')}.aspx"
            }
            transformed.append(transformed_product)
            
        return transformed
    
    def _detect_top_type(self, product: Dict) -> str:
        """Detect specific top type from product data"""
        name = product.get("shortDescription", "").lower()
        
        if any(k in name for k in ["shirt", "button"]):
            return "Shirt"
        elif any(k in name for k in ["t-shirt", "tee"]):
            return "T-Shirt"
        elif any(k in name for k in ["sweater", "pullover"]):
            return "Sweater"
        elif any(k in name for k in ["hoodie", "sweatshirt"]):
            return "Sweatshirt"
        else:
            return "Top"
            
    def _detect_bottom_type(self, product: Dict) -> str:
        """Detect specific bottom type from product data"""
        name = product.get("shortDescription", "").lower()
        
        if any(k in name for k in ["jeans"]):
            return "Jeans"
        elif any(k in name for k in ["shorts"]):
            return "Shorts"
        elif any(k in name for k in ["skirt"]):
            return "Skirt"
        else:
            return "Pants"
    
    def _get_fallback_products(self, category: str, query: str, limit: int = 1) -> List[Dict[str, Any]]:
        """Get fallback products when API fails or no credentials"""
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
                "product_id": f"fallback-top-{query_hash}",
                "product_name": f"{color.capitalize()} Designer T-Shirt",
                "brand": "Luxury Brand",
                "category": "Top",
                "price": 95.0 + (query_hash % 100),
                "image_url": f"https://images.unsplash.com/photo-1576566588028-4147f3842f27?q=80&w=1964&auto=format&fit=crop",
                "description": f"Stylish {color} t-shirt with designer logo",
                "source": "Fallback DB",
                "product_url": "#"
            }]
        elif category == "Bottom":
            return [{
                "product_id": f"fallback-bottom-{query_hash}",
                "product_name": f"{color.capitalize()} Designer Jeans",
                "brand": "Premium Denim",
                "category": "Bottom",
                "price": 145.0 + (query_hash % 100),
                "image_url": f"https://images.unsplash.com/photo-1584370848010-d7fe6bc767ec?q=80&w=1974&auto=format&fit=crop",
                "description": f"Premium {color} jeans with perfect fit",
                "source": "Fallback DB",
                "product_url": "#"
            }]
        elif category == "Shoes":
            return [{
                "product_id": f"fallback-shoes-{query_hash}",
                "product_name": f"{color.capitalize()} Designer Shoes",
                "brand": "Footwear Luxury",
                "category": "Shoes",
                "price": 225.0 + (query_hash % 150),
                "image_url": f"https://images.unsplash.com/photo-1543163521-1bf539c55dd2?q=80&w=1480&auto=format&fit=crop",
                "description": f"Premium {color} shoes for any occasion",
                "source": "Fallback DB",
                "product_url": "#"
            }]
        elif category == "Accessory":
            return [{
                "product_id": f"fallback-accessory-{query_hash}",
                "product_name": f"{color.capitalize()} Designer Accessory",
                "brand": "Accessorize",
                "category": "Accessory",
                "price": 85.0 + (query_hash % 100),
                "image_url": f"https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?q=80&w=1287&auto=format&fit=crop",
                "description": f"Stylish {color} accessory to complete your look",
                "source": "Fallback DB",
                "product_url": "#"
            }]
        elif category == "Dress":
            return [{
                "product_id": f"fallback-dress-{query_hash}",
                "product_name": f"{color.capitalize()} Designer Dress",
                "brand": "Haute Couture",
                "category": "Dress",
                "price": 195.0 + (query_hash % 200),
                "image_url": f"https://images.unsplash.com/photo-1596783074918-c84cb1bd5d44?q=80&w=1974&auto=format&fit=crop",
                "description": f"Elegant {color} dress for special occasions",
                "source": "Fallback DB",
                "product_url": "#"
            }]
        else:
            return [{
                "product_id": f"fallback-item-{query_hash}",
                "product_name": f"{color.capitalize()} Designer Item",
                "brand": "Fashion Brand",
                "category": category,
                "price": 150.0 + (query_hash % 100),
                "image_url": f"https://images.unsplash.com/photo-1578681994506-b8f463449011?q=80&w=1970&auto=format&fit=crop",
                "description": f"Luxury {color} fashion item",
                "source": "Fallback DB",
                "product_url": "#"
            }]

# Create singleton instance
farfetch_service = FarfetchService() 