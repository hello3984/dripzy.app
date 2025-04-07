import os
import httpx
import json
from typing import Dict, List, Optional, Any
from pydantic import BaseModel

class ProductService:
    """Service for fetching products from real external APIs"""
    
    # API keys - in real app would be loaded from env vars
    amazon_api_key = os.getenv("AMAZON_API_KEY")
    amazon_api_secret = os.getenv("AMAZON_API_SECRET")
    asos_api_key = os.getenv("ASOS_API_KEY")
    shopify_api_key = os.getenv("SHOPIFY_API_KEY")
    shopify_store = os.getenv("SHOPIFY_STORE")
    
    # Use mock data if no API keys are provided
    use_mock_data = not (amazon_api_key or asos_api_key or shopify_api_key)
    
    @staticmethod
    async def search_amazon_products(query: str, category: str = None, max_price: float = None) -> List[Dict[str, Any]]:
        """
        Search for products on Amazon using their Product Advertising API
        
        Args:
            query: Search query
            category: Product category
            max_price: Maximum price
            
        Returns:
            List of products
        """
        if not ProductService.amazon_api_key:
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
                        "Authorization": f"Bearer {ProductService.amazon_api_key}"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # Process Amazon API response into our standard format
                    return ProductService._transform_amazon_products(data)
                else:
                    print(f"Error querying Amazon API: {response.status_code}")
                    return []
                    
        except Exception as e:
            print(f"Exception while querying Amazon API: {str(e)}")
            return []
    
    @staticmethod
    async def search_asos_products(query: str, category: str = None, max_price: float = None) -> List[Dict[str, Any]]:
        """
        Search for products on ASOS using their API
        
        Args:
            query: Search query
            category: Product category
            max_price: Maximum price
            
        Returns:
            List of products
        """
        if not ProductService.asos_api_key:
            return []
            
        try:
            # In a real implementation, you would use the ASOS API
            # This is a placeholder implementation
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.asos.com/products/v2/search",
                    params={
                        "q": query,
                        "categoryId": ProductService._map_category_to_asos(category) if category else None,
                        "maxPrice": max_price
                    },
                    headers={
                        "X-API-Key": ProductService.asos_api_key
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # Process ASOS API response into our standard format
                    return ProductService._transform_asos_products(data)
                else:
                    print(f"Error querying ASOS API: {response.status_code}")
                    return []
                    
        except Exception as e:
            print(f"Exception while querying ASOS API: {str(e)}")
            return []
    
    @staticmethod
    async def search_shopify_products(query: str, category: str = None, max_price: float = None) -> List[Dict[str, Any]]:
        """
        Search for products on a Shopify store
        
        Args:
            query: Search query
            category: Product category
            max_price: Maximum price
            
        Returns:
            List of products
        """
        if not (ProductService.shopify_api_key and ProductService.shopify_store):
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
                    f"https://{ProductService.shopify_store}.myshopify.com/api/2023-01/graphql.json",
                    json={"query": graphql_query, "variables": variables},
                    headers={
                        "X-Shopify-Storefront-Access-Token": ProductService.shopify_api_key
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # Process Shopify API response into our standard format
                    return ProductService._transform_shopify_products(data)
                else:
                    print(f"Error querying Shopify API: {response.status_code}")
                    return []
                    
        except Exception as e:
            print(f"Exception while querying Shopify API: {str(e)}")
            return []
    
    @staticmethod
    async def search_products(
        query: str, 
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for products across multiple sources
        
        Args:
            query: Search query
            filters: Dictionary of filters:
                - sources: List of sources to search (amazon, asos, shopify)
                - category: Product category
                - price_min: Minimum price
                - price_max: Maximum price
                - gender: Target gender (male, female, neutral)
                - limit: Maximum number of results
            
        Returns:
            List of products
        """
        if ProductService.use_mock_data:
            return ProductService._get_mock_products(
                query, 
                filters.get('category', None) if filters else None,
                filters.get('price_max', None) if filters else None,
                filters.get('limit', 20) if filters else 20
            )
            
        # Otherwise, search from actual API sources
        sources = filters.get('sources', ['amazon', 'asos', 'shopify']) if filters else ['amazon', 'asos', 'shopify']
        category = filters.get('category', None) if filters else None
        max_price = filters.get('price_max', None) if filters else None
        limit = filters.get('limit', 20) if filters else 20
        
        all_products = []
        
        # Fetch from all selected sources
        if 'amazon' in sources:
            amazon_products = await ProductService.search_amazon_products(query, category, max_price)
            all_products.extend(amazon_products)
            
        if 'asos' in sources:
            asos_products = await ProductService.search_asos_products(query, category, max_price)
            all_products.extend(asos_products)
            
        if 'shopify' in sources:
            shopify_products = await ProductService.search_shopify_products(query, category, max_price)
            all_products.extend(shopify_products)
            
        # Apply gender filter if specified
        if filters and 'gender' in filters and filters['gender']:
            gender = filters['gender'].lower()
            if gender != 'neutral':
                all_products = [p for p in all_products if p.get('gender', 'neutral').lower() == gender 
                                 or p.get('gender', 'neutral').lower() == 'neutral']
        
        # Apply minimum price filter if specified
        if filters and 'price_min' in filters and filters['price_min'] is not None:
            min_price = float(filters['price_min'])
            all_products = [p for p in all_products if p.get('price', 0) >= min_price]
        
        # Sort by relevance (in a real app, you might have a more sophisticated algorithm)
        # For now, just prioritize products where the query appears in the name
        all_products.sort(key=lambda p: 1 if query.lower() in p.get('name', '').lower() else 0, reverse=True)
        
        # Return limited results
        return all_products[:limit]

    @staticmethod
    async def get_clothing_items_by_category(
        categories: List[str],
        style_keywords: List[str],
        filters: Dict[str, Any] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get clothing items organized by category, matching style keywords
        
        Args:
            categories: List of clothing categories to fetch
            style_keywords: List of style descriptors to match
            filters: Additional filters (gender, price range, etc.)
            
        Returns:
            Dictionary of products organized by category
        """
        result = {}
        
        for category in categories:
            # Create a search query combining category and style keywords
            query = f"{category} {' '.join(style_keywords[:3])}"  # Use top 3 keywords
            
            category_filters = filters.copy() if filters else {}
            category_filters['category'] = category
            category_filters['limit'] = 5  # Limit to top 5 per category
            
            items = await ProductService.search_products(query, category_filters)
            
            # Add source for overlay image that would be used in virtual try-on
            for item in items:
                item['overlay_image'] = item.get('image_url')
            
            result[category] = items
            
        return result
    
    @staticmethod
    async def get_clothing_items_for_outfit(
        outfit_style: Dict[str, Any],
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Get clothing items for a complete outfit based on style and preferences
        
        Args:
            outfit_style: Style information with clothing needs
            filters: Additional filters (gender, price range, etc.)
            
        Returns:
            List of clothing items that form a complete outfit
        """
        # Extract categories and options from the outfit style
        categories = []
        options_by_category = {}
        
        for item in outfit_style.get('clothing_items', []):
            if isinstance(item, dict):
                category = item.get('type', '')
                options = item.get('options', [])
                if category:
                    categories.append(category)
                    options_by_category[category] = options
            elif isinstance(item, str):
                # Simple string format - try to categorize
                if 'top' in item or 'shirt' in item or 'blouse' in item:
                    categories.append('top')
                    options_by_category['top'] = [item]
                elif 'bottom' in item or 'pant' in item or 'skirt' in item or 'short' in item:
                    categories.append('bottom')
                    options_by_category['bottom'] = [item]
                elif 'shoe' in item or 'boot' in item or 'sneaker' in item:
                    categories.append('shoes')
                    options_by_category['shoes'] = [item]
                elif 'accessory' in item or 'hat' in item or 'bag' in item or 'jewelry' in item:
                    categories.append('accessory')
                    options_by_category['accessory'] = [item]
        
        # Ensure we have at least essential categories
        essential_categories = ['top', 'bottom', 'shoes']
        for category in essential_categories:
            if category not in categories:
                categories.append(category)
        
        # Use style descriptors for search
        style_keywords = outfit_style.get('style_descriptors', [])
        
        # Get items for each category
        outfit_items = []
        
        for category in categories:
            # Construct search query using category options if available
            if category in options_by_category and options_by_category[category]:
                search_term = f"{options_by_category[category][0]} {' '.join(style_keywords[:2])}"
            else:
                search_term = f"{category} {' '.join(style_keywords[:2])}"
            
            category_filters = filters.copy() if filters else {}
            category_filters['category'] = category
            category_filters['limit'] = 1  # Just get the top match
            
            items = await ProductService.search_products(search_term, category_filters)
            
            if items:
                outfit_items.append(items[0])
        
        return outfit_items
    
    @staticmethod
    def _transform_amazon_products(data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Transform Amazon API response into standardized product format"""
        products = []
        
        # This is a placeholder for the actual transformation logic
        # In a real implementation, you would parse the Amazon API response
        # and convert it to the standard product format
        
        # Example placeholder parsing logic
        for item in data.get('Items', []):
            product = {
                'id': item.get('ASIN'),
                'name': item.get('ItemInfo', {}).get('Title', {}).get('DisplayValue', ''),
                'brand': item.get('ItemInfo', {}).get('ByLineInfo', {}).get('Brand', {}).get('DisplayValue', ''),
                'category': item.get('ItemInfo', {}).get('Classifications', {}).get('ProductGroup', {}).get('DisplayValue', ''),
                'price': float(item.get('Offers', {}).get('Listings', [{}])[0].get('Price', {}).get('Amount', 0)),
                'url': item.get('DetailPageURL', ''),
                'image_url': item.get('Images', {}).get('Primary', {}).get('Large', {}).get('URL', ''),
                'description': item.get('ItemInfo', {}).get('Features', {}).get('DisplayValues', [''])[0],
                'source': 'amazon'
            }
            products.append(product)
            
        return products
    
    @staticmethod
    def _transform_asos_products(data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Transform ASOS API response into standardized product format"""
        products = []
        
        # This is a placeholder for the actual transformation logic
        # In a real implementation, you would parse the ASOS API response
        # and convert it to the standard product format
        
        # Example placeholder parsing logic
        for item in data.get('products', []):
            product = {
                'id': item.get('id'),
                'name': item.get('name', ''),
                'brand': item.get('brandName', ''),
                'category': item.get('productType', {}).get('name', ''),
                'price': item.get('price', {}).get('current', {}).get('value', 0),
                'url': f"https://www.asos.com/{item.get('url', '')}",
                'image_url': item.get('imageUrl', ''),
                'description': item.get('description', ''),
                'source': 'asos'
            }
            products.append(product)
            
        return products
    
    @staticmethod
    def _transform_shopify_products(data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Transform Shopify API response into standardized product format"""
        products = []
        
        # This is a placeholder for the actual transformation logic
        # In a real implementation, you would parse the Shopify API response
        # and convert it to the standard product format
        
        # Example placeholder parsing logic
        for edge in data.get('data', {}).get('products', {}).get('edges', []):
            node = edge.get('node', {})
            
            # Get the first image URL if available
            image_url = ''
            if node.get('images', {}).get('edges', []):
                image_url = node.get('images', {}).get('edges', [])[0].get('node', {}).get('url', '')
            
            product = {
                'id': node.get('id', '').split('/')[-1],  # Extract ID from GraphQL ID
                'name': node.get('title', ''),
                'brand': node.get('vendor', ''),
                'category': node.get('productType', ''),
                'price': float(node.get('priceRange', {}).get('minVariantPrice', {}).get('amount', 0)),
                'url': f"https://{ProductService.shopify_store}.myshopify.com/products/{node.get('handle', '')}",
                'image_url': image_url,
                'description': node.get('description', ''),
                'source': 'shopify'
            }
            products.append(product)
            
        return products
    
    @staticmethod
    def _map_category_to_asos(category: str) -> Optional[str]:
        """Map general category to ASOS category ID"""
        # This is a placeholder mapping
        # In a real implementation, you would have a more complete mapping
        category_map = {
            'top': '4169',  # Women's tops
            'bottom': '2640',  # Women's jeans
            'dress': '8799',  # Women's dresses
            'shoes': '6992',  # Women's shoes
            'accessory': '4174',  # Women's accessories
        }
        
        return category_map.get(category.lower() if category else None)
    
    @staticmethod
    def _get_mock_products(query: str, category: str = None, max_price: float = None, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get mock products for testing
        
        Args:
            query: Search query
            category: Product category
            max_price: Maximum price
            limit: Maximum number of results
            
        Returns:
            List of mock products
        """
        # Basic mock product database
        all_products = [
            # Tops
            {
                'id': 'p1',
                'name': 'Fringe Crop Top',
                'brand': 'ASOS',
                'category': 'top',
                'price': 45.99,
                'url': 'https://www.asos.com/example',
                'image_url': 'https://via.placeholder.com/300x400?text=Fringe+Crop+Top',
                'description': 'Stylish fringe crop top perfect for festivals',
                'source': 'asos',
                'gender': 'female'
            },
            {
                'id': 'p2',
                'name': 'Bohemian Lace Blouse',
                'brand': 'Free People',
                'category': 'top',
                'price': 89.99,
                'url': 'https://www.freepeople.com/example',
                'image_url': 'https://via.placeholder.com/300x400?text=Lace+Blouse',
                'description': 'Boho-chic lace blouse with floral embroidery',
                'source': 'shopify',
                'gender': 'female'
            },
            {
                'id': 'p3',
                'name': 'Classic White T-Shirt',
                'brand': 'GAP',
                'category': 'top',
                'price': 24.99,
                'url': 'https://www.gap.com/example',
                'image_url': 'https://via.placeholder.com/300x400?text=White+T-Shirt',
                'description': 'Versatile white t-shirt for any occasion',
                'source': 'amazon',
                'gender': 'neutral'
            },
            
            # Bottoms
            {
                'id': 'p4',
                'name': 'High-Waisted Denim Shorts',
                'brand': 'H&M',
                'category': 'bottom',
                'price': 29.99,
                'url': 'https://www.hm.com/example',
                'image_url': 'https://via.placeholder.com/300x400?text=Denim+Shorts',
                'description': 'Comfortable denim shorts with vintage wash',
                'source': 'asos',
                'gender': 'female'
            },
            {
                'id': 'p5',
                'name': 'Ripped Skinny Jeans',
                'brand': 'Levi\'s',
                'category': 'bottom',
                'price': 79.99,
                'url': 'https://www.levis.com/example',
                'image_url': 'https://via.placeholder.com/300x400?text=Ripped+Jeans',
                'description': 'Trendy ripped skinny jeans with stretch',
                'source': 'amazon',
                'gender': 'female'
            },
            {
                'id': 'p6',
                'name': 'Flowy Maxi Skirt',
                'brand': 'Anthropologie',
                'category': 'bottom',
                'price': 69.99,
                'url': 'https://www.anthropologie.com/example',
                'image_url': 'https://via.placeholder.com/300x400?text=Maxi+Skirt',
                'description': 'Flowy maxi skirt with bohemian print',
                'source': 'shopify',
                'gender': 'female'
            },
            
            # Shoes
            {
                'id': 'p7',
                'name': 'Western Ankle Boots',
                'brand': 'Amazon',
                'category': 'shoes',
                'price': 89.99,
                'url': 'https://www.amazon.com/example',
                'image_url': 'https://via.placeholder.com/300x400?text=Ankle+Boots',
                'description': 'Stylish western boots with comfortable heel',
                'source': 'amazon',
                'gender': 'female'
            },
            {
                'id': 'p8',
                'name': 'Platform Sandals',
                'brand': 'Steve Madden',
                'category': 'shoes',
                'price': 79.99,
                'url': 'https://www.stevemadden.com/example',
                'image_url': 'https://via.placeholder.com/300x400?text=Platform+Sandals',
                'description': 'Trendy platform sandals with ankle strap',
                'source': 'asos',
                'gender': 'female'
            },
            {
                'id': 'p9',
                'name': 'Canvas Sneakers',
                'brand': 'Converse',
                'category': 'shoes',
                'price': 59.99,
                'url': 'https://www.converse.com/example',
                'image_url': 'https://via.placeholder.com/300x400?text=Canvas+Sneakers',
                'description': 'Classic canvas sneakers with rubber sole',
                'source': 'amazon',
                'gender': 'neutral'
            },
            
            # Accessories
            {
                'id': 'p10',
                'name': 'Oversized Sunglasses',
                'brand': 'Zara',
                'category': 'accessory',
                'price': 19.99,
                'url': 'https://www.zara.com/example',
                'image_url': 'https://via.placeholder.com/300x400?text=Sunglasses',
                'description': 'UV protection oversized sunglasses',
                'source': 'asos',
                'gender': 'neutral'
            },
            {
                'id': 'p11',
                'name': 'Wide Brim Hat',
                'brand': 'Urban Outfitters',
                'category': 'accessory',
                'price': 39.99,
                'url': 'https://www.urbanoutfitters.com/example',
                'image_url': 'https://via.placeholder.com/300x400?text=Wide+Brim+Hat',
                'description': 'Boho-style wide brim hat with ribbon',
                'source': 'shopify',
                'gender': 'female'
            },
            {
                'id': 'p12',
                'name': 'Layered Necklace Set',
                'brand': 'Forever 21',
                'category': 'accessory',
                'price': 14.99,
                'url': 'https://www.forever21.com/example',
                'image_url': 'https://via.placeholder.com/300x400?text=Layered+Necklace',
                'description': 'Gold-tone layered necklace set with pendants',
                'source': 'amazon',
                'gender': 'female'
            }
        ]
        
        # Filter by category if specified
        if category:
            all_products = [p for p in all_products if p['category'].lower() == category.lower()]
            
        # Filter by price if specified
        if max_price is not None:
            all_products = [p for p in all_products if p['price'] <= max_price]
            
        # Filter by query (basic text search)
        if query:
            query_lower = query.lower()
            filtered_products = []
            
            # First priority: exact matches in name
            for product in all_products:
                if query_lower in product['name'].lower():
                    filtered_products.append(product)
                    
            # Second priority: matches in description
            for product in all_products:
                if product not in filtered_products and query_lower in product['description'].lower():
                    filtered_products.append(product)
                    
            # Fall back to special keywords for festival/coachella
            if 'festival' in query_lower or 'coachella' in query_lower:
                festival_keywords = ['bohemian', 'fringe', 'crop', 'western', 'flowy', 'oversized']
                for product in all_products:
                    if product not in filtered_products:
                        for keyword in festival_keywords:
                            if keyword in product['name'].lower() or keyword in product['description'].lower():
                                filtered_products.append(product)
                                break
            
            all_products = filtered_products if filtered_products else all_products
        
        # Return limited results
        return all_products[:limit] 