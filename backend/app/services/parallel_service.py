"""
Parallel API Service
-------------------
High-performance concurrent API processing for product searches.
This module maintains compatibility with existing code but dramatically improves performance.
"""

import asyncio
import logging
import uuid
from typing import List, Dict, Any, Optional
from functools import lru_cache
import time
import re
import os
import json
import aiohttp

from app.core.cache import cache_service
from app.services.serpapi_service import SerpAPIService
from app.core.config import settings
from app.core.connection_pool import get_connection_pool

# Configure logging
logger = logging.getLogger(__name__)

# In-memory cache with TTL to avoid repeated API calls
_api_cache = {}
_CACHE_TTL = 3600  # 1 hour in seconds

class ParallelSearchService:
    """
    Service for performing concurrent product searches.
    Improves performance by parallelizing independent API calls.
    """
    
    def __init__(self):
        self.serpapi_service = SerpAPIService(settings)
        self.semaphore = asyncio.Semaphore(5)  # Limit concurrent requests to 5
        self._cache = {}
        self._cache_ttl = 3600  # 1 hour cache TTL
        self._cache_hits = 0
        self._cache_misses = 0
        self._connection_pool = None
        self._semaphore = asyncio.Semaphore(10)  # Limit concurrent requests
    
    async def search_products_parallel(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Search for products in parallel using concurrent API calls
        
        Args:
            items: List of items to search for
            
        Returns:
            Enhanced items with product details
        """
        try:
            if not items:
                logger.warning("No items provided for parallel search")
                return []
                
            # Create search tasks for all items
            tasks = []
            for item in items:
                # Generate a search query from item attributes
                query = self._create_optimized_search_query(item)
                
                # Add original index to maintain order
                if "original_index" not in item:
                    item["original_index"] = len(tasks)
                
                # Create task with semaphore to limit concurrency
                tasks.append(self._search_product_with_semaphore(item, query))
            
            # Execute all tasks concurrently with gather
            logger.info(f"Running {len(tasks)} product searches in parallel")
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            # Process results, handling any exceptions
            enhanced_items = []
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Error in parallel search: {str(result)}")
                    continue
                enhanced_items.append(result)
                
            logger.info(f"Parallel search completed in {end_time - start_time:.2f} seconds")
            
            # Sort by original index to maintain order
            enhanced_items.sort(key=lambda x: x.get("original_index", 0))
            return enhanced_items
            
        except Exception as e:
            logger.error(f"Error in parallel product search: {str(e)}")
            return items  # Return original items on error for safety
    
    async def _search_product_with_semaphore(self, item: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Search for product with semaphore to limit concurrent connections"""
        try:
            async with self.semaphore:
                # Check in-memory cache first
                cache_key = f"product:{query}:{item.get('category', '')}"
                cached_result = self._get_cached_result(cache_key)
                
                if cached_result:
                    # Apply cached product data to this item
                    return {**item, **cached_result, "source": "cache"}
                
                # Perform API search with category
                products = await self.serpapi_service.search_products(
                    query=query,
                    category=item.get("category"),
                    num_products=1  # We only need the best match
                )
                
                if products and len(products) > 0:
                    product = products[0]
                    # Cache the result
                    self._set_cached_result(cache_key, product)
                    
                    # Enhance the item with product details
                    return {**item, **product, "matched_query": query}
                else:
                    logger.warning(f"No products found for query: {query}")
                    return item
        except Exception as e:
            logger.error(f"Error in product search for {query}: {str(e)}")
            return item  # Return original item on error
    
    def _create_optimized_search_query(self, item: Dict[str, Any]) -> str:
        """
        Create an optimized search query from item attributes.
        Prioritizes the most specific attributes for better matches.
        """
        query_parts = []
        
        # Add category as a prefix if available
        if item.get("category"):
            query_parts.append(item["category"])
            
        # Add color if available
        if item.get("color"):
            query_parts.append(item["color"])
            
        # Add name or description
        if item.get("name"):
            query_parts.append(item["name"])
        elif item.get("description"):
            # Use only first 30 chars of description for relevance
            query_parts.append(item["description"][:30])
            
        # Add search keywords if specified
        if item.get("search_keywords"):
            search_keywords = item["search_keywords"]
            # Handle both string and list formats for search_keywords
            if isinstance(search_keywords, list):
                # Add up to 3 keywords from list to avoid query bloat
                for keyword in search_keywords[:3]:
                    if keyword and isinstance(keyword, str):
                        query_parts.append(keyword.strip())
            elif isinstance(search_keywords, str):
                # Add the keywords string directly
                query_parts.append(search_keywords.strip())
            else:
                # Try to convert to string for any other type
                try:
                    query_parts.append(str(search_keywords).strip())
                except:
                    logger.warning(f"Could not process search_keywords: {search_keywords}")
            
        # Join with spaces and limit length
        query = " ".join(query_parts).strip()
        
        # Clean up query by removing common filler words
        query = re.sub(r'\b(a|an|the|with|for|and|or|that|this|these|those)\b', ' ', query, flags=re.IGNORECASE)
        query = re.sub(r'\s+', ' ', query).strip()
        
        return query[:100]  # Limit query length
    
    def _get_cached_result(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached result if not expired"""
        if key in _api_cache:
            timestamp, data = _api_cache[key]
            if time.time() - timestamp < _CACHE_TTL:
                logger.debug(f"Cache hit for {key}")
                return data
        return None
        
    def _set_cached_result(self, key: str, data: Dict[str, Any]) -> None:
        """Cache result with timestamp"""
        _api_cache[key] = (time.time(), data)
        
        # Cleanup old cache entries (prevent memory growth)
        if len(_api_cache) > 1000:
            now = time.time()
            expired_keys = [k for k, (ts, _) in _api_cache.items() 
                          if now - ts > _CACHE_TTL]
            for key in expired_keys[:100]:  # Remove oldest 100 items
                del _api_cache[key]

    async def _search_product_with_retry(self, query: str, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Search for a product with retry logic
        
        Args:
            query: Search query string
            item: Original item data
            
        Returns:
            Product data or None if not found
        """
        # Check cache first
        cache_key = f"{query}_{item.get('category', '')}"
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            self._cache_hits += 1
            logger.debug(f"Cache hit for query: {query}")
            return cached_result
        
        self._cache_misses += 1
        
        # Not in cache, perform actual search
        max_retries = 3
        retry_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                async with self._semaphore:
                    result = await self._perform_search(query, item)
                    
                    if result:
                        # Cache successful result
                        self._add_to_cache(cache_key, result)
                        return result
                    
                    # No result, but API call was successful
                    logger.debug(f"No products found for query: {query}")
                    return None
                    
            except Exception as e:
                logger.warning(f"Search attempt {attempt+1} failed for query '{query}': {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
        
        logger.error(f"All search attempts failed for query: {query}")
        return None
    
    async def _perform_search(self, query: str, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Perform actual product search using the API"""
        # Implementation depends on your search API
        # This is a placeholder
        try:
            # SERPAPI implementation would go here
            await asyncio.sleep(0.1)  # Simulate API call delay
            
            # For now, return mock data
            return {
                "product_id": f"mock-{hash(query) % 10000}",
                "product_name": item.get("name", "Unknown Product"),
                "brand": "Example Brand",
                "price": 29.99,
                "currency": "USD",
                "image_url": "https://example.com/product.jpg",
                "product_url": "https://example.com/product",
            }
        except Exception as e:
            logger.error(f"Search API error: {str(e)}")
            raise
    
    def _get_from_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """Get item from cache if it exists and is not expired"""
        if key in self._cache:
            timestamp, data = self._cache[key]
            if time.time() - timestamp < self._cache_ttl:
                return data
            # Expired entry
            del self._cache[key]
        return None
    
    def _add_to_cache(self, key: str, data: Dict[str, Any]) -> None:
        """Add item to cache with current timestamp"""
        self._cache[key] = (time.time(), data)
        
        # Basic cache size management - clear if too large
        if len(self._cache) > 1000:
            # Remove oldest 20% of entries
            entries = sorted(self._cache.items(), key=lambda x: x[1][0])
            for k, _ in entries[:int(len(entries) * 0.2)]:
                del self._cache[k]
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "size": len(self._cache),
            "hits": self._cache_hits,
            "misses": self._cache_misses,
            "hit_ratio": self._cache_hits / (self._cache_hits + self._cache_misses) if (self._cache_hits + self._cache_misses) > 0 else 0
        }

# Singleton instance for use throughout the app
parallel_search_service = ParallelSearchService()

# Expose a simple function to get the service
def get_parallel_search_service():
    return parallel_search_service 