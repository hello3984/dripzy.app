import os
import httpx
import json
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
import logging

from app.services.serpapi_service import serpapi_service
from app.services.skimlinks_service import SkimlinksService
from app.core.cache import cache_service
from app.core.config import settings

class ProductService:
    """Service for fetching products from real external APIs"""
    
    def __init__(self):
        """Initialize the product service with API keys from environment variables"""
        self.amazon_api_key = os.getenv("AMAZON_API_KEY")
        self.amazon_api_secret = os.getenv("AMAZON_API_SECRET")
        self.asos_api_key = os.getenv("ASOS_API_KEY")
        self.shopify_api_key = os.getenv("SHOPIFY_API_KEY")
        self.shopify_store = os.getenv("SHOPIFY_STORE")
        
        # Default to mock data if no API keys are provided
        self.use_mock_data = not (self.amazon_api_key or self.asos_api_key or self.shopify_api_key)
    
    async def search_amazon_products(self, query: str, category: str = None, max_price: float = None) -> List[Dict[str, Any]]:
        """
        Search for products on Amazon using their Product Advertising API
        
        Args:
            query: Search query
            category: Product category
            max_price: Maximum price
            
        Returns:
            List of products
        """
        if not self.amazon_api_key:
            return []
            
        try:
            # In a real implementation, you would use the Amazon Product Advertising API
            # Example with httpx (you'll need to implement the actual Amazon API requirements)
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://webservices.amazon.com/paapi5/searchitems",
                    params={
                        "Keywords": query,
                        "SearchIndex": category or "Fashion",
                        "MaxPrice": str(int(max_price * 100)) if max_price else None
                    },
                    headers={
                        "Authorization": f"Bearer {self.amazon_api_key}"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # Process Amazon API response into our standard format
                    return self._transform_amazon_products(data)
                else:
                    print(f"Error querying Amazon API: {response.status_code}")
                    return []
                    
        except Exception as e:
            print(f"Exception while querying Amazon API: {str(e)}")
            return []
    
    async def search_asos_products(self, query: str, category: str = None, max_price: float = None) -> List[Dict[str, Any]]:
        """
        Search for products on ASOS using their API
        
        Args:
            query: Search query
            category: Product category
            max_price: Maximum price
            
        Returns:
            List of products
        """
        if not self.asos_api_key:
            return []
            
        try:
            # In a real implementation, you would use the ASOS API
            # This is a placeholder implementation
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.asos.com/products/v2/search",
                    params={
                        "q": query,
                        "categoryId": self._map_category_to_asos(category) if category else None,
                        "maxPrice": max_price
                    },
                    headers={
                        "X-API-Key": self.asos_api_key
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # Process ASOS API response into our standard format
                    return self._transform_asos_products(data)
                else:
                    print(f"Error querying ASOS API: {response.status_code}")
                    return []
                    
        except Exception as e:
            print(f"Exception while querying ASOS API: {str(e)}")
            return []
    
    async def search_shopify_products(self, query: str, category: str = None, max_price: float = None) -> List[Dict[str, Any]]:
        """
        Search for products on a Shopify store
        
        Args:
            query: Search query
            category: Product category
            max_price: Maximum price
            
        Returns:
            List of products
        """
        if not (self.shopify_api_key and self.shopify_store):
            return []
            
        try:
            # In a real implementation, you would use the Shopify Storefront API
            # Example GraphQL query
            graphql_query = """
            {
              products(first: 10, query: $query) {
                edges {
                  node {
                    id
                    title
                    description
                    vendor
                    productType
                    priceRange {
                      minVariantPrice {
                        amount
                      }
                    }
                    images(first: 1) {
                      edges {
                        node {
                          url
                        }
                      }
                    }
                  }
                }
              }
            }
            """
            
            variables = {
                "query": query + (f" AND product_type:{category}" if category else "") +
                          (f" AND price:<={max_price}" if max_price else "")
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://{self.shopify_store}.myshopify.com/api/2023-01/graphql.json",
                    json={"query": graphql_query, "variables": variables},
                    headers={
                        "X-Shopify-Storefront-Access-Token": self.shopify_api_key
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # Process Shopify API response into our standard format
                    return self._transform_shopify_products(data)
                else:
                    print(f"Error querying Shopify API: {response.status_code}")
                    return []
                    
        except Exception as e:
            print(f"Exception while querying Shopify API: {str(e)}")
            return []
    
    async def search_products(self, 
                              query: str, 
                              sources: List[str] = None,
                              category: str = None, 
                              max_price: float = None,
                              limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search for products across multiple sources
        
        Args:
            query: Search query
            sources: List of sources to search (amazon, asos, shopify)
            category: Product category
            max_price: Maximum price
            limit: Maximum number of results
            
        Returns:
            List of products
        """
        if self.use_mock_data:
            return self._get_mock_products(query, category, max_price, limit)
            
        # Default to all available sources
        if not sources:
            sources = []
            if self.amazon_api_key:
                sources.append("amazon")
            if self.asos_api_key:
                sources.append("asos")
            if self.shopify_api_key and self.shopify_store:
                sources.append("shopify")
                
        # If we still don't have any sources, return mock data
        if not sources:
            return self._get_mock_products(query, category, max_price, limit)
        
        # Search all specified sources
        all_products = []
        
        if "amazon" in sources:
            amazon_products = await self.search_amazon_products(query, category, max_price)
            for product in amazon_products:
                product["source"] = "amazon"
            all_products.extend(amazon_products)
            
        if "asos" in sources:
            asos_products = await self.search_asos_products(query, category, max_price)
            for product in asos_products:
                product["source"] = "asos"
            all_products.extend(asos_products)
            
        if "shopify" in sources:
            shopify_products = await self.search_shopify_products(query, category, max_price)
            for product in shopify_products:
                product["source"] = "shopify"
            all_products.extend(shopify_products)
            
        # Limit results
        return all_products[:limit]
    
    def _transform_amazon_products(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Transform Amazon API response to our standard product format"""
        products = []
        
        # This is a placeholder implementation - you'll need to adapt to the actual Amazon API response format
        items = data.get("Items", [])
        
        for item in items:
            product = {
                "id": item.get("ASIN", ""),
                "name": item.get("ItemInfo", {}).get("Title", {}).get("DisplayValue", ""),
                "brand": item.get("ItemInfo", {}).get("ByLineInfo", {}).get("Brand", {}).get("DisplayValue", ""),
                "category": item.get("ItemInfo", {}).get("Classifications", {}).get("Binding", {}).get("DisplayValue", ""),
                "price": float(item.get("Offers", {}).get("Listings", [{}])[0].get("Price", {}).get("Amount", 0)),
                "url": item.get("DetailPageURL", ""),
                "image_url": item.get("Images", {}).get("Primary", {}).get("Large", {}).get("URL", ""),
                "description": item.get("ItemInfo", {}).get("Features", {}).get("DisplayValues", [""])[0],
                "tags": []
            }
            products.append(product)
            
        return products
    
    def _transform_asos_products(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Transform ASOS API response to our standard product format"""
        products = []
        
        # This is a placeholder implementation - you'll need to adapt to the actual ASOS API response format
        items = data.get("products", [])
        
        for item in items:
            product = {
                "id": str(item.get("id", "")),
                "name": item.get("name", ""),
                "brand": item.get("brandName", ""),
                "category": item.get("productType", {}).get("name", ""),
                "price": float(item.get("price", {}).get("current", {}).get("value", 0)),
                "url": f"https://www.asos.com/{item.get('url')}",
                "image_url": item.get("imageUrl", ""),
                "description": item.get("description", ""),
                "tags": [category.get("name") for category in item.get("categoryNames", [])]
            }
            products.append(product)
            
        return products
    
    def _transform_shopify_products(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Transform Shopify API response to our standard product format"""
        products = []
        
        # This is a placeholder implementation - you'll need to adapt to the actual Shopify API response format
        edges = data.get("data", {}).get("products", {}).get("edges", [])
        
        for edge in edges:
            node = edge.get("node", {})
            price = float(node.get("priceRange", {}).get("minVariantPrice", {}).get("amount", 0))
            
            images = node.get("images", {}).get("edges", [])
            image_url = images[0].get("node", {}).get("url", "") if images else ""
            
            product = {
                "id": node.get("id", "").split("/")[-1],
                "name": node.get("title", ""),
                "brand": node.get("vendor", ""),
                "category": node.get("productType", ""),
                "price": price,
                "url": f"https://{self.shopify_store}.myshopify.com/products/{node.get('handle')}",
                "image_url": image_url,
                "description": node.get("description", ""),
                "tags": []
            }
            products.append(product)
            
        return products
    
    def _map_category_to_asos(self, category: str) -> Optional[str]:
        """Map our category names to ASOS category IDs"""
        # This is a placeholder - you would need the actual ASOS category mapping
        category_map = {
            "top": "4169",
            "bottom": "4208",
            "dress": "8799",
            "shoes": "4172",
            "accessory": "4174"
        }
        return category_map.get(category.lower())
    
    def _get_mock_products(self, query: str, category: str = None, max_price: float = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Get mock product data for when APIs are not configured"""
        from app.routers.products import get_mock_products
        
        # Get all mock products
        all_products = get_mock_products()
        
        # Filter by query
        if query:
            query = query.lower()
            all_products = [p for p in all_products if 
                          query in p["name"].lower() or 
                          query in p.get("description", "").lower()]
        
        # Filter by category
        if category:
            all_products = [p for p in all_products if p["category"] == category]
        
        # Filter by price
        if max_price is not None:
            all_products = [p for p in all_products if p["price"] <= max_price]
            
        # Return limited results
        return all_products[:limit] 