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
import urllib.parse

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
            # Get connection pool manager and use it properly
            pool_manager = get_connection_pool()
            
            # Make the request using httpx directly
            async with httpx.AsyncClient(timeout=10.0, verify=certifi.where()) as client:
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
            
            # Get direct product URL with better extraction
            product_url = self._extract_product_url(result)
            
            # If no direct URL available, create smart retailer URLs
            if not product_url:
                product_url = self._create_smart_retailer_url(result, category)
            
            # Get high-quality image URL
            image_url = self._get_best_image_url(result)
            
            # Extract better brand information
            brand = self._extract_brand(result)
            
            # Standardize product fields
            product = {
                "product_id": product_id,
                "product_name": result.get("title", "Product Name"),
                "brand": brand,
                "category": category or "General",
                "price": price,
                "image_url": image_url,
                "product_url": product_url,
                "currency": "USD",
                "description": result.get("snippet", ""),
                "source": "serpapi",
                "retailer": self._identify_retailer(product_url)
            }
            
            products.append(product)
        
        return products
    
    def _extract_product_url(self, result: Dict[str, Any]) -> str:
        """Extract the real product URL from SerpAPI result with enhanced detection."""
        logger.debug(f"Extracting URL from result keys: {list(result.keys())}")
        
        # Priority 1: Check for direct product link
        product_url = result.get("link", "")
        
        # Priority 2: Check for merchant-specific links
        if not product_url and "merchant" in result:
            merchant = result["merchant"]
            if isinstance(merchant, dict) and "link" in merchant:
                product_url = merchant["link"]
                logger.debug(f"Found merchant link: {product_url}")
        
        # Priority 3: Check for extracted/cleaned URLs
        if not product_url:
            url_candidates = [
                result.get("product_link"),
                result.get("extracted_url"), 
                result.get("source_link"),
                result.get("redirect_link")
            ]
            
            for candidate in url_candidates:
                if candidate and isinstance(candidate, str) and candidate.startswith("http"):
                    product_url = candidate
                    logger.debug(f"Found candidate URL: {product_url}")
                    break
        
        if not product_url:
            logger.warning("No direct URL found in SerpAPI result, will create smart retailer URL")
            return ""
        
        logger.debug(f"Raw product URL: {product_url}")
        
        # Clean up Google Shopping redirect URLs
        if "google.com/shopping/product" in product_url or "google.com/url" in product_url:
            cleaned_url = self._extract_real_url_from_google_redirect(product_url)
            if cleaned_url:
                logger.debug(f"Cleaned Google redirect URL: {cleaned_url}")
                return cleaned_url
        
        # Validate the URL points to a real retailer
        if self._is_real_retailer_url(product_url):
            logger.debug(f"Validated retailer URL: {product_url}")
            return product_url
        
        logger.debug(f"URL not from known retailer, will create smart URL instead: {product_url}")
        return ""
    
    def _extract_real_url_from_google_redirect(self, google_url: str) -> str:
        """Extract real retailer URL from Google Shopping redirect."""
        try:
            import urllib.parse
            
            # Method 1: Extract from 'url=' parameter
            if "url=" in google_url:
                parts = google_url.split("url=")
                if len(parts) > 1:
                    encoded_url = parts[1].split("&")[0]
                    real_url = urllib.parse.unquote(encoded_url)
                    if real_url.startswith("http") and self._is_real_retailer_url(real_url):
                        return real_url
            
            # Method 2: Extract from 'q=' parameter
            if "q=" in google_url:
                parts = google_url.split("q=")
                if len(parts) > 1:
                    encoded_url = parts[1].split("&")[0] 
                    real_url = urllib.parse.unquote(encoded_url)
                    if real_url.startswith("http") and self._is_real_retailer_url(real_url):
                        return real_url
            
            # Method 3: Look for any complete URLs in the redirect
            import re
            url_pattern = r'https?://[^\s&]+\.[a-z]{2,}[^\s&]*'
            urls = re.findall(url_pattern, google_url)
            
            for url in urls:
                if self._is_real_retailer_url(url):
                    return url.rstrip('"\')')
            
        except Exception as e:
            logger.error(f"Error extracting real URL from Google redirect: {str(e)}")
        
        return ""
    
    def _is_real_retailer_url(self, url: str) -> bool:
        """Check if URL points to a real retailer (not search engines)."""
        if not url or not isinstance(url, str):
            return False
        
        url_lower = url.lower()
        
        # Exclude search engines and generic platforms
        excluded_domains = [
            "google.com", "bing.com", "yahoo.com", "duckduckgo.com",
            "shopping.com", "shop.com", "pricerunner.com", "shopzilla.com"
        ]
        
        for domain in excluded_domains:
            if domain in url_lower:
                return False
        
        # Include known fashion retailers
        retailer_domains = [
            "nordstrom.com", "farfetch.com", "amazon.com", "zara.com", "hm.com",
            "uniqlo.com", "gap.com", "jcrew.com", "madewell.com", "everlane.com",
            "cos.com", "arket.com", "macys.com", "saks.com", "bloomingdales.com",
            "neimanmarcus.com", "barneys.com", "mrporter.com", "net-a-porter.com",
            "ssense.com", "matchesfashion.com", "revolve.com", "asos.com",
            "shopbop.com", "intermixonline.com", "forward.com"
        ]
        
        for domain in retailer_domains:
            if domain in url_lower:
                return True
        
        # If it's a product page URL (contains product indicators), likely valid
        product_indicators = ["/product/", "/p/", "/item/", "/shop/", "/buy/", "/products/", "-p-"]
        for indicator in product_indicators:
            if indicator in url_lower:
                return True
        
        return False
    
    def _get_best_image_url(self, result: Dict[str, Any]) -> str:
        """Get the best quality image URL from the result."""
        # Try different image fields in order of preference
        image_fields = ["thumbnail", "image", "images"]
        
        for field in image_fields:
            if field in result and result[field]:
                image_url = result[field]
                # If it's a list, take the first one
                if isinstance(image_url, list) and image_url:
                    return image_url[0]
                elif isinstance(image_url, str):
                    return image_url
        
        return ""
    
    def _extract_brand(self, result: Dict[str, Any]) -> str:
        """Extract brand name from the result."""
        # Try different brand fields
        if "brand" in result and result["brand"]:
            return result["brand"]
        
        # Try to extract from source
        source = result.get("source", "")
        if source and source != "Shopping":
            return source
        
        # Try to extract from title
        title = result.get("title", "")
        # Look for brand patterns in title
        common_brands = [
            "Nike", "Adidas", "Zara", "H&M", "Uniqlo", "Gap", "Banana Republic",
            "J.Crew", "Madewell", "Everlane", "COS", "Arket", "Massimo Dutti",
            "Nordstrom", "Saks", "Bloomingdale's", "Macy's", "Target", "Walmart"
        ]
        
        for brand in common_brands:
            if brand.lower() in title.lower():
                return brand
        
        return "Fashion Brand"
    
    def _identify_retailer(self, url: str) -> str:
        """Identify the retailer from the product URL."""
        if not url:
            return "Unknown"
        
        url_lower = url.lower()
        
        retailers = {
            "nordstrom.com": "Nordstrom",
            "farfetch.com": "Farfetch",
            "amazon.com": "Amazon",
            "zara.com": "Zara",
            "hm.com": "H&M",
            "uniqlo.com": "Uniqlo",
            "gap.com": "Gap",
            "jcrew.com": "J.Crew",
            "madewell.com": "Madewell",
            "everlane.com": "Everlane",
            "cos.com": "COS",
            "arket.com": "Arket",
            "macys.com": "Macy's",
            "saks.com": "Saks Fifth Avenue",
            "bloomingdales.com": "Bloomingdale's"
        }
        
        for domain, retailer in retailers.items():
            if domain in url_lower:
                return retailer
        
        return "Online Store"
    
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

    def _extract_price(self, price_str: str) -> float:
        """
        Extract a clean float price from a price string.
        
        Args:
            price_str: Price string like "$29.99", "€45", etc.
            
        Returns:
            Float price value
        """
        try:
            if not price_str:
                return 29.99  # Default price
            
            # Remove currency symbols and commas
            clean_price = price_str.replace('$', '').replace('€', '').replace('£', '')
            clean_price = clean_price.replace(',', '').replace(' ', '').strip()
            
            # Extract just the numbers and decimal point
            import re
            match = re.search(r'(\d+\.\d+|\d+)', clean_price)
            if match:
                clean_price = match.group(0)
            else:
                return 29.99
            
            price = float(clean_price)
            # Sanity check on price range
            if price < 0.1 or price > 10000:
                return 29.99
            return price
        except (ValueError, TypeError):
            return 29.99  # Default price on error

    def _create_smart_retailer_url(self, result: Dict[str, Any], category: str = None) -> str:
        """Create smart retailer search URLs when direct URLs aren't available."""
        title = result.get("title", "")
        brand = self._extract_brand(result)
        
        # Extract key product details
        product_keywords = self._extract_product_keywords(title, brand, category)
        
        # Create search query
        search_query = " ".join(product_keywords)
        encoded_query = urllib.parse.quote_plus(search_query)
        
        # Choose retailer based on category and brand
        retailer_url = self._choose_best_retailer_url(brand, category, encoded_query)
        
        logger.info(f"Created smart retailer URL for '{title}': {retailer_url}")
        return retailer_url
    
    def _extract_product_keywords(self, title: str, brand: str, category: str) -> List[str]:
        """Extract relevant keywords for retailer search."""
        keywords = []
        
        # Add brand if available and not generic
        if brand and brand not in ["Fashion Brand", "Amazon.com - Seller", "Shopping"]:
            keywords.append(brand)
        
        # Add category-specific terms
        if category:
            category_terms = {
                "Top": ["shirt", "blouse", "top"],
                "Bottom": ["pants", "jeans", "shorts", "skirt"],
                "Dress": ["dress"],
                "Shoes": ["shoes", "sneakers", "boots"],
                "Accessory": ["bag", "jewelry", "accessories"],
                "Outerwear": ["jacket", "coat"]
            }
            
            if category in category_terms:
                keywords.extend(category_terms[category][:1])  # Add one category term
        
        # Extract key words from title (excluding brand)
        title_words = title.lower().split()
        
        # Remove common generic words
        stop_words = {
            "women's", "men's", "unisex", "for", "with", "the", "and", "or", 
            "size", "color", "style", "fashion", "new", "sale", "best", "top", "quality"
        }
        
        # Add important descriptive words
        important_words = []
        for word in title_words:
            clean_word = word.strip(".,!?()[]")
            if (len(clean_word) > 3 and 
                clean_word not in stop_words and 
                not clean_word.isdigit() and
                clean_word not in brand.lower()):
                important_words.append(clean_word)
        
        # Add up to 3 most relevant title words
        keywords.extend(important_words[:3])
        
        return keywords
    
    def _choose_best_retailer_url(self, brand: str, category: str, encoded_query: str) -> str:
        """Choose the best retailer based on brand and category with enhanced targeting."""
        
        # High-end/luxury brands -> Prioritize Farfetch (like competitor)
        luxury_brands = {
            "cinq a sept", "cinq à sept", "gucci", "prada", "versace", "balenciaga", 
            "saint laurent", "bottega veneta", "celine", "loewe", "jacquemus", 
            "ganni", "staud", "khaite", "isabel marant", "acne studios", "helmut lang",
            "theory", "vince", "rag & bone", "proenza schouler", "3.1 phillip lim"
        }
        
        # Premium contemporary brands -> Nordstrom or Farfetch
        contemporary_brands = {
            "theory", "vince", "rag & bone", "helmut lang", "acne studios",
            "cos", "arket", "everlane", "reformation", "ganni", "sandro", "maje"
        }
        
        # Athletic/streetwear brands -> Nordstrom or brand direct
        athletic_brands = {
            "nike", "adidas", "puma", "new balance", "asics", "vans", "converse",
            "off-white", "stone island", "kenzo", "palm angels"
        }
        
        # Accessible luxury brands -> Nordstrom
        accessible_brands = {
            "zara", "h&m", "uniqlo", "gap", "banana republic", "j.crew", 
            "madewell", "everlane", "cos", "arket", "massimo dutti"
        }
        
        brand_lower = brand.lower()
        
        # Enhanced retailer selection logic
        if any(luxury_brand in brand_lower for luxury_brand in luxury_brands):
            # Luxury brands - prioritize Farfetch (matches competitor strategy)
            return f"https://www.farfetch.com/shopping/search/items.aspx?q={encoded_query}&storeid=9359"
        
        elif any(contemporary_brand in brand_lower for contemporary_brand in contemporary_brands):
            # Contemporary brands - use Nordstrom (excellent contemporary selection)
            return f"https://www.nordstrom.com/sr?keyword={encoded_query}&origin=keywordsearch"
        
        elif any(athletic_brand in brand_lower for athletic_brand in athletic_brands):
            # Athletic brands - use Nordstrom (comprehensive athletic selection)
            return f"https://www.nordstrom.com/sr?keyword={encoded_query}&origin=keywordsearch"
        
        elif any(accessible_brand in brand_lower for accessible_brand in accessible_brands):
            # Accessible brands - use Nordstrom
            return f"https://www.nordstrom.com/sr?keyword={encoded_query}&origin=keywordsearch"
        
        else:
            # Default strategy - alternate between Farfetch and Nordstrom
            # This ensures variety and matches competitor's multi-retailer approach
            import hashlib
            hash_value = int(hashlib.md5(brand_lower.encode()).hexdigest(), 16)
            
            if hash_value % 2 == 0:
                return f"https://www.farfetch.com/shopping/search/items.aspx?q={encoded_query}&storeid=9359"
            else:
                return f"https://www.nordstrom.com/sr?keyword={encoded_query}&origin=keywordsearch"

# --- Removed global instance creation ---
# No longer create the instance here
# serpapi_service = SerpAPIService()
# --------------------------------------- 

# Create the global instance with settings
serpapi_service = SerpAPIService(api_key=settings.SERPAPI_API_KEY) 