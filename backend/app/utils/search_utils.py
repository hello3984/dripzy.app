import asyncio
import logging
import random
import time
from typing import Dict, Any, Optional, List
import aiohttp
import os
import re

logger = logging.getLogger(__name__)

# Configuration
MAX_RETRIES = 3
RETRY_DELAY_BASE = 2  # seconds
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY", "")
SEARCH_API_ENDPOINT = "https://serpapi.com/search.json"

def create_search_query(item: Dict[str, Any]) -> str:
    """
    Create an optimized search query from item attributes
    
    Args:
        item: Item dictionary with attributes
        
    Returns:
        Optimized search query string
    """
    # Start with search keywords if available
    search_keywords = item.get("search_keywords", "")
    
    # Handle both list and string types for search_keywords
    if isinstance(search_keywords, list):
        query = " ".join(search_keywords) if search_keywords else ""
    else:
        query = search_keywords
    
    # Use description as a fallback
    if not query and "description" in item:
        query = item["description"]
    
    # Add color if available and not 'unknown'
    if item.get("color") and item.get("color").lower() != "unknown":
        query += f" {item['color']}"
    
    # Add category if available and not 'unknown'
    if item.get("category") and item.get("category").lower() != "unknown":
        query += f" {item['category']}"
    
    # Add brand if available and not 'unknown'
    if item.get("brand") and item.get("brand").lower() != "unknown":
        query += f" {item['brand']}"
    
    # Optimize the query
    return optimize_search_query(query)

def optimize_search_query(query: str) -> str:
    """
    Optimize a search query by removing unnecessary words and limiting length
    
    Args:
        query: Raw query string
        
    Returns:
        Optimized query string
    """
    # List of stop words to remove
    stop_words = [
        "a", "an", "the", "of", "in", "on", "with", "and", "or", "for", 
        "to", "that", "this", "these", "those", "at", "by", "as",
        "from", "about", "like", "such", "be", "is", "are", "was", "were"
    ]
    
    # Split the query into words
    words = query.split()
    
    # Filter out stop words and empty strings
    filtered_words = [word for word in words if word.lower() not in stop_words and word.strip()]
    
    # Limit to a reasonable number of terms (6-8 is typically good for product searches)
    if len(filtered_words) > 7:
        filtered_words = filtered_words[:7]
    
    # Join the filtered words back into a query string
    optimized_query = " ".join(filtered_words)
    
    return optimized_query

async def search_product_with_retry(query: str, max_retries: int = MAX_RETRIES) -> Optional[Dict[str, Any]]:
    """
    Search for a product with retry logic
    
    Args:
        query: Search query string
        max_retries: Maximum number of retry attempts
        
    Returns:
        Product data dictionary or None if not found/error
    """
    attempt = 0
    
    while attempt < max_retries:
        try:
            # Perform the search
            result = await search_product(query)
            
            # If we got a valid result, return it
            if result:
                return result
            
            # If no result, increment attempt and retry
            attempt += 1
            
            # Add some jitter to avoid overloading the API
            delay = RETRY_DELAY_BASE * (attempt ** 2) + random.uniform(0, 1)
            logger.info(f"No product found for query: '{query}'. Retrying in {delay:.2f} seconds... (Attempt {attempt}/{max_retries})")
            
            # Wait before retrying
            await asyncio.sleep(delay)
            
        except Exception as e:
            # Log the error
            logger.error(f"Error searching for product: {str(e)}")
            
            # Increment attempt count
            attempt += 1
            
            # Calculate exponential backoff with jitter
            delay = RETRY_DELAY_BASE * (attempt ** 2) + random.uniform(0, 1)
            logger.info(f"Error in product search. Retrying in {delay:.2f} seconds... (Attempt {attempt}/{max_retries})")
            
            # Wait before retrying
            await asyncio.sleep(delay)
    
    # If we've exhausted all retries, return None
    logger.warning(f"Failed to find product for query '{query}' after {max_retries} attempts")
    return None

async def search_product(query: str) -> Optional[Dict[str, Any]]:
    """
    Search for a product using the search API
    
    Args:
        query: Search query string
        
    Returns:
        Product data or None if not found
    """
    try:
        # Check if API key is available
        if not SERPAPI_API_KEY:
            logger.warning("SERPAPI_API_KEY not set. Using mock product data.")
            return create_mock_product_data(query)
        
        # Prepare the search parameters
        params = {
            "q": f"{query} buy online",
            "api_key": SERPAPI_API_KEY,
            "engine": "google",
            "tbm": "shop"  # Shopping results
        }
        
        # Make the API request
        async with aiohttp.ClientSession() as session:
            async with session.get(SEARCH_API_ENDPOINT, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract the first shopping result
                    shopping_results = data.get("shopping_results", [])
                    if shopping_results and len(shopping_results) > 0:
                        result = shopping_results[0]
                        
                        # Build a structured result
                        product_data = {
                            "title": result.get("title", ""),
                            "link": result.get("link", ""),
                            "price": result.get("price", ""),
                            "thumbnail": result.get("thumbnail", ""),
                            "source": result.get("source", "")
                        }
                        
                        return product_data
                    else:
                        logger.info(f"No shopping results found for query: '{query}'")
                        return None
                else:
                    logger.error(f"API error: {response.status} for query '{query}'")
                    return None
    
    except Exception as e:
        logger.error(f"Exception in search_product for query '{query}': {str(e)}")
        return None

def create_mock_product_data(query: str) -> Dict[str, Any]:
    """
    Create mock product data for testing without an API key
    
    Args:
        query: Search query string
        
    Returns:
        Mock product data
    """
    # Extract key terms from the query
    words = query.lower().split()
    
    # Determine probable category
    categories = ["shirt", "pants", "jacket", "shoes", "dress", "sweater", "jeans", "hat", "coat"]
    category = next((word for word in words if word in categories), "clothing")
    
    # Determine probable color
    colors = ["black", "white", "blue", "red", "green", "yellow", "brown", "pink", "purple", "gray"]
    color = next((word for word in words if word in colors), "")
    
    # Create a title
    title = f"{color.capitalize() if color else 'Classic'} {category.capitalize()}"
    
    # Random price between $19.99 and $199.99
    price = f"${(random.randint(1999, 19999) / 100):.2f}"
    
    # Mock data with the product details
    return {
        "title": title,
        "link": f"https://example.com/products/{category}",
        "price": price,
        "thumbnail": f"https://example.com/images/{category}.jpg",
        "source": "MockShop"
    }

def _create_optimized_search_query(item: Dict[str, Any]) -> str:
    """
    Create an optimized search query from item attributes.
    
    Args:
        item: Item dictionary with attributes
        
    Returns:
        Optimized search query string
    """
    query_parts = []
    
    # Add category as a prefix if available
    if item.get("category"):
        query_parts.append(item["category"])
        
    # Add color if available
    if item.get("color"):
        query_parts.append(item["color"])
        
    # Add name or description - prioritize name as it's usually more specific
    if item.get("name"):
        query_parts.append(item["name"])
    elif item.get("description"):
        # Use only first 30 chars of description for relevance
        query_parts.append(item["description"][:30])
        
    # Add search keywords if specified
    if item.get("search_keywords"):
        if isinstance(item["search_keywords"], list):
            query_parts.extend(item["search_keywords"][:3])  # Add top 3 keywords
        else:
            query_parts.append(str(item["search_keywords"]))
            
    # Join parts and remove common filler words to improve search relevance
    query = " ".join(query_parts).strip()
    
    # Clean up and optimize the query
    query = re.sub(r'\b(a|an|the|with|for|and|or|that|this|these|those)\b', ' ', query, flags=re.IGNORECASE)
    query = re.sub(r'\s+', ' ', query).strip()
    
    # Limit query length to 100 chars for better API results
    return query[:100] if len(query) > 100 else query 