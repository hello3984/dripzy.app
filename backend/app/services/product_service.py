import asyncio
import logging
import os
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import aiohttp
import traceback
import time
from ..utils.search_utils import create_search_query, search_product_with_retry

logger = logging.getLogger(__name__)

class ParallelProductSearchService:
    """Service for searching products in parallel to improve performance"""
    
    @staticmethod
    async def search_products_parallel(items: List[Dict[str, Any]], max_workers: int = 8) -> List[Dict[str, Any]]:
        """
        Search for products in parallel using a thread pool
        
        Args:
            items: List of item dictionaries to search for
            max_workers: Maximum number of concurrent workers
            
        Returns:
            List of enhanced items with product details
        """
        if not items:
            return []
            
        # Limit max workers to the number of items and a reasonable upper bound
        max_workers = min(max_workers, len(items), 10)
        logger.info(f"Starting parallel product search with {max_workers} workers for {len(items)} items")
        
        # Create a semaphore to limit concurrent API calls
        semaphore = asyncio.Semaphore(max_workers)
        
        # Create a list to store the tasks
        tasks = []
        
        start_time = time.time()
        
        # Create a task for each item
        for item in items:
            task = asyncio.create_task(
                ParallelProductSearchService._search_item_with_semaphore(item, semaphore)
            )
            tasks.append(task)
        
        # Wait for all tasks to complete
        enhanced_items = await asyncio.gather(*tasks)
        
        elapsed_time = time.time() - start_time
        logger.info(f"Parallel product search completed in {elapsed_time:.2f} seconds")
        
        return enhanced_items
    
    @staticmethod
    async def _search_item_with_semaphore(item: Dict[str, Any], semaphore: asyncio.Semaphore) -> Dict[str, Any]:
        """
        Search for a product with semaphore to limit concurrent requests
        
        Args:
            item: Item dictionary to search for
            semaphore: Semaphore to limit concurrent requests
            
        Returns:
            Enhanced item with product details
        """
        async with semaphore:
            try:
                # Get search query for the item
                query = create_search_query(item)
                
                # Search for product with retry
                search_result = await search_product_with_retry(query)
                
                # Enhance item with search result
                enhanced_item = item.copy()
                
                if search_result:
                    enhanced_item["product_url"] = search_result.get("link", "")
                    enhanced_item["image_url"] = search_result.get("thumbnail", "")
                    enhanced_item["price"] = search_result.get("price", "")
                    enhanced_item["source"] = search_result.get("source", "")
                    enhanced_item["title"] = search_result.get("title", "")
                else:
                    # If no result, add empty values
                    enhanced_item["product_url"] = ""
                    enhanced_item["image_url"] = ""
                    enhanced_item["price"] = ""
                    enhanced_item["source"] = ""
                    enhanced_item["title"] = ""
                
                return enhanced_item
            except Exception as e:
                logger.error(f"Error searching for item {item.get('description', 'unknown')}: {str(e)}")
                logger.error(traceback.format_exc())
                
                # Return original item if search fails
                return item 