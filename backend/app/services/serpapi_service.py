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
        excluded_brands = ["shein", "temu"]  # Completely blocked brands
        
        # Filter out excluded brands BEFORE processing
        filtered_results = []
        for result in results:
            # Extract brand, source, and title for checking
            brand = self._extract_brand(result).lower()
            source = result.get("source", "").lower()
            title = result.get("title", "").lower()
            
            # Skip if any excluded brand is detected
            is_excluded = (
                any(excluded_brand in brand for excluded_brand in excluded_brands) or
                any(excluded_brand in source for excluded_brand in excluded_brands) or
                any(excluded_brand in title for excluded_brand in excluded_brands)
            )
            
            if is_excluded:
                logger.info(f"🚫 EXCLUDED BRAND FILTERED OUT: {result.get('title', 'Unknown')} - Brand: {brand}")
                continue  # Skip this product completely
            
            filtered_results.append(result)
        
        # Take only the requested number of results from filtered list
        filtered_results = filtered_results[:limit]
        
        for result in filtered_results:
            # Generate a unique product ID
            product_id = f"serpapi-{uuid.uuid4()}"
            
            # Extract price as a float
            price = self._extract_price(result.get("price", "0"))
            
            # ENHANCED URL STRATEGY: Always create retailer search URLs
            # SerpAPI often doesn't provide direct product URLs, so we create our own
            product_url = self._create_direct_retailer_product_url(result, category)
            
            # Fallback: Try to extract from SerpAPI if direct creation fails
            if not product_url:
                product_url = self._extract_product_url(result)
            
            # Final fallback: Create smart retailer search URLs
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
        """Get the highest quality product image URL - prioritizing actual retailer images."""
        
        # PRIORITY 1: Try to extract actual retailer product images
        product_url = self._extract_product_url(result)
        if product_url and self._is_real_retailer_url(product_url):
            actual_image = self._extract_retailer_product_image(product_url, result)
            if actual_image:
                logger.info(f"✅ Found actual retailer image: {actual_image[:60]}...")
                return actual_image
        
        # PRIORITY 2: Look for high-quality images in SerpAPI data
        high_quality_image = self._find_high_quality_serpapi_image(result)
        if high_quality_image:
            logger.info(f"✅ Found high-quality SerpAPI image: {high_quality_image[:60]}...")
            return high_quality_image
        
        # PRIORITY 3: Standard SerpAPI thumbnails as fallback
        image_fields = ["thumbnail", "image", "images"]
        
        for field in image_fields:
            if field in result and result[field]:
                image_url = result[field]
                if isinstance(image_url, list) and image_url:
                    logger.info(f"🔄 Using SerpAPI thumbnail: {image_url[0][:60]}...")
                    return image_url[0]
                elif isinstance(image_url, str):
                    logger.info(f"🔄 Using SerpAPI thumbnail: {image_url[:60]}...")
                    return image_url
        
        # PRIORITY 4: Generate high-quality placeholder
        title = result.get("title", "Product")
        category = result.get("category", "Fashion")
        placeholder_url = f"https://via.placeholder.com/400x500/f8f9fa/333333?text={urllib.parse.quote(title[:20])}"
        logger.warning(f"⚠️ No images found, using placeholder: {placeholder_url}")
        return placeholder_url
    
    def _extract_retailer_product_image(self, product_url: str, result: Dict[str, Any]) -> str:
        """Extract actual product image from retailer website using real-time scraping."""
        try:
            url_domain = self._extract_domain(product_url)
            
            # PRIORITY 1: Try to scrape actual product image from retailer page
            scraped_image = self._scrape_product_image_from_url(product_url, url_domain)
            if scraped_image:
                logger.info(f"🔥 SCRAPED ACTUAL RETAILER IMAGE: {scraped_image[:60]}...")
                return scraped_image
            
            # PRIORITY 2: Look for better images in SerpAPI result linked to retailer
            all_images = []
            
            # Collect all possible image URLs
            for field in ["thumbnail", "image", "images", "rich_snippet"]:
                field_data = result.get(field)
                if field_data:
                    if isinstance(field_data, list):
                        all_images.extend([img for img in field_data if isinstance(img, str)])
                    elif isinstance(field_data, str):
                        all_images.append(field_data)
                    elif isinstance(field_data, dict):
                        # Sometimes images are nested in objects
                        for key, value in field_data.items():
                            if key in ["image", "thumbnail", "url"] and isinstance(value, str):
                                all_images.append(value)
            
            # Filter for high-quality images (larger dimensions or better domains)
            for image_url in all_images:
                if self._is_high_quality_image(image_url, url_domain):
                    logger.info(f"📸 FOUND HIGH-QUALITY SERPAPI IMAGE: {image_url[:60]}...")
                    return image_url
            
            # PRIORITY 3: Construct direct retailer image URL using patterns
            constructed_image = self._construct_retailer_image_url(product_url, result)
            if constructed_image:
                logger.info(f"🔧 CONSTRUCTED RETAILER IMAGE: {constructed_image[:60]}...")
                return constructed_image
            
            return ""
            
        except Exception as e:
            logger.error(f"Error extracting retailer image from {product_url}: {str(e)}")
            return ""
    
    def _scrape_product_image_from_url(self, product_url: str, domain: str) -> str:
        """Scrape actual product image from retailer website."""
        try:
            # Quick implementation for major retailers
            # In production, you'd want more robust scraping with proper headers, delays, etc.
            
            import httpx
            import re
            from bs4 import BeautifulSoup
            
            # Set up headers to mimic a real browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            # Quick scrape with timeout to avoid blocking the API
            with httpx.Client(timeout=5.0, headers=headers) as client:
                response = client.get(product_url)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Retailer-specific image selectors
                    image_selectors = {
                        "nordstrom.com": [
                            'img[data-testid="product-image"]',
                            'img[class*="product-image"]',
                            'img[class*="ProductImage"]',
                            'img[alt*="product"]'
                        ],
                        "farfetch.com": [
                            'img[data-testid="product-image"]',
                            'img[class*="ProductImage"]',
                            'img[class*="product-shot"]',
                            'picture img'
                        ],
                        "amazon.com": [
                            '#landingImage',
                            'img[data-a-image-name="landingImage"]',
                            'img[class*="product-image"]',
                            'img[id*="product"]'
                        ],
                        "zara.com": [
                            'img[class*="product-detail-image"]',
                            'img[class*="media-image"]',
                            'picture img'
                        ]
                    }
                    
                    # Try retailer-specific selectors
                    for retailer_domain, selectors in image_selectors.items():
                        if retailer_domain in domain:
                            for selector in selectors:
                                img_element = soup.select_one(selector)
                                if img_element:
                                    img_src = img_element.get('src') or img_element.get('data-src')
                                    if img_src:
                                        # Make sure it's a full URL
                                        if img_src.startswith('//'):
                                            img_src = 'https:' + img_src
                                        elif img_src.startswith('/'):
                                            img_src = f"https://{domain}{img_src}"
                                        
                                        # Validate it's a good image URL
                                        if self._is_valid_product_image_url(img_src):
                                            return img_src
                    
                    # Fallback: look for any high-quality product images
                    all_imgs = soup.find_all('img')
                    for img in all_imgs:
                        img_src = img.get('src') or img.get('data-src')
                        if img_src and self._is_valid_product_image_url(img_src):
                            alt_text = img.get('alt', '').lower()
                            # Check if it looks like a product image
                            if any(keyword in alt_text for keyword in ['product', 'item', 'clothing', 'shirt', 'dress', 'shoes', 'bag']):
                                if img_src.startswith('//'):
                                    img_src = 'https:' + img_src
                                elif img_src.startswith('/'):
                                    img_src = f"https://{domain}{img_src}"
                                return img_src
                                
        except Exception as e:
            logger.warning(f"Could not scrape image from {product_url}: {str(e)}")
        
        return ""
    
    def _is_valid_product_image_url(self, img_src: str) -> bool:
        """Check if an image URL looks like a valid product image."""
        if not img_src or not isinstance(img_src, str):
            return False
        
        img_lower = img_src.lower()
        
        # Must be a proper image URL
        if not any(ext in img_lower for ext in ['.jpg', '.jpeg', '.png', '.webp']):
            return False
        
        # Exclude obvious non-product images
        exclude_indicators = [
            'logo', 'icon', 'banner', 'header', 'footer', 'nav', 'menu',
            'social', 'facebook', 'twitter', 'instagram', 'pinterest',
            'newsletter', 'email', 'search', 'cart', 'checkout',
            'placeholder', '1x1', 'tracking', 'pixel'
        ]
        
        if any(indicator in img_lower for indicator in exclude_indicators):
            return False
        
        # Prefer larger images
        size_indicators = ['large', 'xl', '800', '1000', '1200', 'main', 'primary']
        has_size_indicator = any(indicator in img_lower for indicator in size_indicators)
        
        # Must have reasonable dimensions (not tiny icons)
        if any(tiny in img_lower for tiny in ['16x16', '32x32', '50x50', 'small', 'thumb']):
            return False
        
        return True
    
    def _find_high_quality_serpapi_image(self, result: Dict[str, Any]) -> str:
        """Find the highest quality image from SerpAPI data."""
        all_images = []
        
        # Collect all images from different fields
        image_sources = [
            result.get("thumbnail"),
            result.get("image"), 
            result.get("images"),
            result.get("rich_snippet", {}).get("image") if isinstance(result.get("rich_snippet"), dict) else None
        ]
        
        for source in image_sources:
            if source:
                if isinstance(source, list):
                    all_images.extend([img for img in source if isinstance(img, str)])
                elif isinstance(source, str):
                    all_images.append(source)
        
        # Score images by quality indicators
        best_image = ""
        best_score = 0
        
        for image_url in all_images:
            score = self._score_image_quality(image_url)
            if score > best_score:
                best_score = score
                best_image = image_url
        
        return best_image
    
    def _is_high_quality_image(self, image_url: str, retailer_domain: str = "") -> bool:
        """Check if an image URL appears to be high quality."""
        if not image_url:
            return False
        
        url_lower = image_url.lower()
        
        # Prefer images from known retailers
        if retailer_domain and retailer_domain in url_lower:
            return True
        
        # Look for high-quality image indicators
        quality_indicators = [
            "_large", "_big", "_xl", "_high", "_hd", "_main", 
            "/large/", "/big/", "/xl/", "/high/", "/hd/", "/main/",
            "1200x", "800x", "600x", "original"
        ]
        
        return any(indicator in url_lower for indicator in quality_indicators)
    
    def _score_image_quality(self, image_url: str) -> int:
        """Score an image URL based on quality indicators."""
        if not image_url:
            return 0
        
        score = 0
        url_lower = image_url.lower()
        
        # Higher score for retail domains
        retail_domains = ["nordstrom", "farfetch", "zara", "hm", "uniqlo", "amazon", "asos"]
        for domain in retail_domains:
            if domain in url_lower:
                score += 50
                break
        
        # Score based on size indicators
        size_indicators = {
            "_xl": 40, "_large": 35, "_big": 30, "_medium": 20, "_small": 10,
            "/xl/": 40, "/large/": 35, "/big/": 30, "/medium/": 20, "/small/": 10,
            "1200x": 45, "800x": 35, "600x": 25, "400x": 15, "200x": 5
        }
        
        for indicator, points in size_indicators.items():
            if indicator in url_lower:
                score += points
                break
        
        # Bonus for HTTPS
        if image_url.startswith("https://"):
            score += 10
        
        # Penalty for obvious thumbnails
        thumbnail_indicators = ["thumb", "small", "tiny", "mini", "preview"]
        for indicator in thumbnail_indicators:
            if indicator in url_lower:
                score -= 20
        
        return score
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except:
            return ""
    
    def _construct_retailer_image_url(self, product_url: str, result: Dict[str, Any]) -> str:
        """Extract actual retailer product images using advanced techniques."""
        try:
            domain = self._extract_domain(product_url)
            title = result.get("title", "").lower()
            
            # STRATEGY 1: Look for high-res images in SerpAPI rich data
            rich_snippet = result.get("rich_snippet", {})
            if isinstance(rich_snippet, dict):
                # Check for product gallery or main images
                for key in ["image", "images", "main_image", "product_image"]:
                    if key in rich_snippet and rich_snippet[key]:
                        image_candidate = rich_snippet[key]
                        if isinstance(image_candidate, str) and self._is_high_quality_image(image_candidate, domain):
                            logger.info(f"✅ Found rich snippet image: {image_candidate[:60]}...")
                            return image_candidate
            
            # STRATEGY 2: Extract from known retailer image patterns
            retailer_image = self._extract_known_retailer_image(product_url, result, domain)
            if retailer_image:
                return retailer_image
            
            # STRATEGY 3: Use product ID to construct retailer image URLs
            return self._construct_retailer_specific_image_url(product_url, result, domain)
            
        except Exception as e:
            logger.error(f"Error constructing retailer image URL: {str(e)}")
            return ""
    
    def _extract_known_retailer_image(self, product_url: str, result: Dict[str, Any], domain: str) -> str:
        """Extract images using known retailer URL patterns."""
        
        # Known high-quality image patterns for major retailers
        retailer_patterns = {
            "nordstrom.com": {
                "indicators": ["_images", "_img", "/images/", "/img/"],
                "quality_params": ["?$pdp$", "?$large$", "?$zoom$", "_large", "_xl"]
            },
            "farfetch.com": {
                "indicators": ["cdn-images", "image", "/images/"],
                "quality_params": ["_large", "_xl", "_main", "?w=800", "?w=600"]
            },
            "amazon.com": {
                "indicators": ["images-amazon", "m.media-amazon", "images/I/"],
                "quality_params": ["._SL1000_", "._SL800_", "._SL600_", "._AC_"]
            },
            "zara.com": {
                "indicators": ["/images/", "/static/"],
                "quality_params": ["_large", "_xl", "_main", "?w=800"]
            }
        }
        
        # Check if we have patterns for this retailer
        for retailer_domain, patterns in retailer_patterns.items():
            if retailer_domain in domain:
                # Look through all available images for ones matching this retailer's patterns
                all_images = self._collect_all_images_from_result(result)
                
                for image_url in all_images:
                    # Check if image URL contains retailer indicators
                    if any(indicator in image_url.lower() for indicator in patterns["indicators"]):
                        # Try to enhance the image URL with quality parameters
                        enhanced_url = self._enhance_image_url_quality(image_url, patterns["quality_params"])
                        if enhanced_url:
                            logger.info(f"✅ Enhanced {retailer_domain} image: {enhanced_url[:60]}...")
                            return enhanced_url
                        else:
                            logger.info(f"✅ Found {retailer_domain} image: {image_url[:60]}...")
                            return image_url
        
        return ""
    
    def _collect_all_images_from_result(self, result: Dict[str, Any]) -> List[str]:
        """Collect all possible image URLs from SerpAPI result."""
        all_images = []
        
        # Standard image fields
        for field in ["thumbnail", "image", "images"]:
            field_data = result.get(field)
            if field_data:
                if isinstance(field_data, list):
                    all_images.extend([img for img in field_data if isinstance(img, str)])
                elif isinstance(field_data, str):
                    all_images.append(field_data)
        
        # Rich snippet images
        rich_snippet = result.get("rich_snippet", {})
        if isinstance(rich_snippet, dict):
            for key, value in rich_snippet.items():
                if "image" in key.lower() and isinstance(value, str):
                    all_images.append(value)
        
        # Product gallery or additional images
        for field in ["product_images", "gallery", "media"]:
            if field in result and result[field]:
                field_data = result[field]
                if isinstance(field_data, list):
                    all_images.extend([img for img in field_data if isinstance(img, str)])
        
        return list(set(all_images))  # Remove duplicates
    
    def _create_direct_retailer_product_url(self, result: Dict[str, Any], category: str) -> str:
        """Create direct retailer product URLs that can be scraped for images."""
        try:
            title = result.get("title", "")
            brand = self._extract_brand(result)
            
            # Extract key product details for search
            product_keywords = self._extract_search_keywords(title, brand, category)
            search_query = " ".join(product_keywords)
            
            # Choose retailer based on brand and category (like competitor does)
            chosen_retailer = self._choose_optimal_retailer(brand, category, search_query)
            
            # Create search URL that leads to actual product pages
            if chosen_retailer == "nordstrom":
                search_url = f"https://www.nordstrom.com/sr?keyword={urllib.parse.quote_plus(search_query)}&origin=keywordsearch"
            elif chosen_retailer == "farfetch":
                # FIXED: Use working Farfetch URL format
                search_url = f"https://www.farfetch.com/shopping/search/?q={urllib.parse.quote_plus(search_query)}"
            elif chosen_retailer == "amazon":
                search_url = f"https://www.amazon.com/s?k={urllib.parse.quote_plus(search_query)}&ref=sr_pg_1"
            else:
                return ""
            
            # Try to get the first product from the search results
            actual_product_url = self._extract_first_product_from_search(search_url, chosen_retailer)
            
            if actual_product_url:
                logger.info(f"🎯 CREATED DIRECT RETAILER URL: {actual_product_url[:60]}...")
                return actual_product_url
            else:
                # Return the search URL as fallback (still better than nothing)
                logger.info(f"🔍 USING RETAILER SEARCH URL: {search_url[:60]}...")
                return search_url
                
        except Exception as e:
            logger.error(f"Error creating direct retailer URL: {str(e)}")
            return ""
    
    def _extract_search_keywords(self, title: str, brand: str, category: str) -> List[str]:
        """Extract optimal search keywords for retailer search."""
        keywords = []
        
        # Add brand if it's a real brand (not generic)
        if brand and brand not in ["Fashion Brand", "Amazon.com - Seller", "API Unavailable", "Shopping"]:
            # Clean up brand name
            clean_brand = brand.replace("Amazon.com - Seller", "").replace("'s", "").strip()
            if clean_brand:
                keywords.append(clean_brand)
        
        # Extract descriptive words from title
        title_words = title.lower().split()
        
        # Important fashion descriptors
        fashion_descriptors = [
            "linen", "cotton", "silk", "wool", "cashmere", "denim", "leather",
            "casual", "formal", "short", "long", "sleeve", "sleeveless",
            "button", "down", "polo", "crew", "neck", "v-neck", "round",
            "slim", "regular", "relaxed", "fitted", "oversized",
            "high", "low", "waisted", "rise", "boot", "cut", "straight",
            "skinny", "wide", "leg", "crop", "ankle", "knee", "length"
        ]
        
        # Add relevant descriptors from title
        for word in title_words:
            clean_word = word.strip(".,!?()[]\"'")
            if clean_word in fashion_descriptors or len(clean_word) > 4:
                if clean_word not in keywords and clean_word not in ["women", "men", "womens", "mens"]:
                    keywords.append(clean_word)
                    
                # Limit to most relevant keywords
                if len(keywords) >= 5:
                    break
        
        # Add category-specific terms
        category_terms = {
            "Top": ["shirt"],
            "Bottom": ["pants"],
            "Dress": ["dress"],
            "Shoes": ["shoes"],
            "Outerwear": ["jacket"]
        }
        
        if category in category_terms and category_terms[category][0] not in " ".join(keywords).lower():
            keywords.append(category_terms[category][0])
        
        return keywords[:4]  # Limit to 4 most relevant keywords
    
    def _choose_optimal_retailer(self, brand: str, category: str, search_query: str) -> str:
        """FARFETCH-FIRST retailer selection - prioritizes Farfetch for all products."""
        brand_lower = brand.lower() if brand else ""
        query_lower = search_query.lower()
        
        # FARFETCH-FIRST APPROACH: Always try Farfetch first for best selection
        # Only use exceptions for very specific cases
        
        # Exception 1: Direct Amazon sellers (when product is already from Amazon)
        if "amazon" in brand_lower or "seller" in brand_lower:
            return "amazon"
        
        # Exception 2: Ultra-budget brands (Shein/Temu completely excluded)
        ultra_budget_brands = ["wish", "aliexpress"]
        excluded_brands = ["shein", "temu"]  # These brands are completely blocked
        
        # Block excluded brands completely - return Farfetch (but they shouldn't appear)
        if any(brand_name in brand_lower for brand_name in excluded_brands):
            return "farfetch"  # Excluded brands forced to Farfetch but should be filtered out
            
        if any(brand_name in brand_lower for brand_name in ultra_budget_brands):
            return "nordstrom"
        
        # Exception 3: Athletic brands that are better represented on Nordstrom
        athletic_brands = ["nike", "adidas", "under armour", "lululemon", "athleta", "reebok"]
        if any(brand_name in brand_lower for brand_name in athletic_brands) and any(keyword in query_lower for keyword in ["workout", "gym", "athletic", "sportswear"]):
            return "nordstrom"
        
        # DEFAULT: Use Farfetch for all other cases (luxury, designer, contemporary, casual, etc.)
        # This includes: Saint Laurent, Gucci, Prada, Zara, H&M, J.Crew, Theory, etc.
        return "farfetch"
    
    def _extract_first_product_from_search(self, search_url: str, retailer: str) -> str:
        """Extract the first actual product URL from retailer search results."""
        try:
            import httpx
            from bs4 import BeautifulSoup
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            with httpx.Client(timeout=3.0, headers=headers) as client:
                response = client.get(search_url)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Retailer-specific product link selectors
                    product_selectors = {
                        "nordstrom": [
                            'a[data-testid="product-card-link"]',
                            'a[href*="/p/"]',
                            'a[href*="/product/"]'
                        ],
                        "farfetch": [
                            'a[href*="/shopping/"]',
                            'a[data-testid="product-card"]'
                        ],
                        "amazon": [
                            'a[href*="/dp/"]',
                            'a[href*="/gp/product/"]',
                            'h2 a[href*="/dp/"]'
                        ]
                    }
                    
                    selectors = product_selectors.get(retailer, [])
                    for selector in selectors:
                        link_element = soup.select_one(selector)
                        if link_element:
                            href = link_element.get('href')
                            if href:
                                # Make sure it's a full URL
                                if href.startswith('/'):
                                    domain_map = {
                                        "nordstrom": "https://www.nordstrom.com",
                                        "farfetch": "https://www.farfetch.com",
                                        "amazon": "https://www.amazon.com"
                                    }
                                    href = domain_map.get(retailer, "") + href
                                
                                if href.startswith("http"):
                                    return href
                                    
        except Exception as e:
            logger.warning(f"Could not extract product from search results: {str(e)}")
        
        return ""
    
    def _enhance_image_url_quality(self, image_url: str, quality_params: List[str]) -> str:
        """Enhance image URL with quality parameters."""
        base_url = image_url
        
        # Try to add quality parameters that don't already exist
        for param in quality_params:
            if param not in image_url:
                if "?" in param:
                    # Query parameter
                    separator = "&" if "?" in base_url else "?"
                    enhanced_url = f"{base_url}{separator}{param.lstrip('?')}"
                    return enhanced_url
                else:
                    # URL modification (replace existing size indicators)
                    if "_small" in base_url or "_thumb" in base_url:
                        enhanced_url = base_url.replace("_small", param).replace("_thumb", param)
                        return enhanced_url
                    elif "." in base_url:
                        # Insert before file extension
                        parts = base_url.rsplit(".", 1)
                        if len(parts) == 2:
                            enhanced_url = f"{parts[0]}{param}.{parts[1]}"
                            return enhanced_url
        
        return ""
    
    def _construct_retailer_specific_image_url(self, product_url: str, result: Dict[str, Any], domain: str) -> str:
        """Construct retailer-specific image URLs using product patterns."""
        
        # Extract potential product ID from URL
        import re
        
        # Common product ID patterns
        id_patterns = [
            r'/product/([A-Za-z0-9\-_]+)',
            r'/p/([A-Za-z0-9\-_]+)',
            r'/item/([A-Za-z0-9\-_]+)',
            r'product[_-]?id[=:]([A-Za-z0-9\-_]+)',
            r'/([A-Za-z0-9]{8,})'  # Long alphanumeric strings
        ]
        
        product_id = None
        for pattern in id_patterns:
            match = re.search(pattern, product_url)
            if match:
                product_id = match.group(1)
                break
        
        if not product_id:
            return ""
        
        # Retailer-specific image URL construction
        if "nordstrom.com" in domain:
            # Nordstrom image pattern
            return f"https://n.nordstrommedia.com/id/{product_id}_images/crop/large.jpg"
        elif "farfetch.com" in domain:
            # Farfetch image pattern
            return f"https://cdn-images.farfetch-contents.com/{product_id}_large.jpg"
        elif "amazon.com" in domain:
            # Amazon image pattern
            return f"https://m.media-amazon.com/images/I/{product_id}._AC_SL1000_.jpg"
        
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
        """FARFETCH-FIRST URL selection - always prioritizes Farfetch URLs."""
        
        brand_lower = brand.lower()
        
        # FARFETCH-FIRST APPROACH: Use Farfetch for almost everything
        # Only very specific exceptions use other retailers
        
        # Exception 1: Ultra-budget brands (Shein/Temu completely excluded)
        ultra_budget_brands = ["wish", "aliexpress", "forever 21"]
        excluded_brands = ["shein", "temu"]  # These brands are completely blocked
        
        # Block excluded brands completely - force Farfetch (but they shouldn't appear)
        if any(brand_name in brand_lower for brand_name in excluded_brands):
            # FIXED: Use working Farfetch URL format
            return f"https://www.farfetch.com/shopping/search/?q={encoded_query}"
            
        if any(brand_name in brand_lower for brand_name in ultra_budget_brands):
            return f"https://www.nordstrom.com/sr?keyword={encoded_query}&origin=keywordsearch"
        
        # Exception 2: Athletic brands for sportswear context
        athletic_brands = ["nike", "adidas", "under armour", "lululemon", "athleta", "reebok", "puma", "new balance"]
        if any(brand_name in brand_lower for brand_name in athletic_brands):
            return f"https://www.nordstrom.com/sr?keyword={encoded_query}&origin=keywordsearch"
        
        # DEFAULT: Use Farfetch for ALL other brands
        # FIXED: Use working Farfetch URL format without deprecated parameters
        return f"https://www.farfetch.com/shopping/search/?q={encoded_query}"

# --- Removed global instance creation ---
# No longer create the instance here
# serpapi_service = SerpAPIService()
# --------------------------------------- 

# Create the global instance with settings
serpapi_service = SerpAPIService(api_key=settings.SERPAPI_API_KEY) 