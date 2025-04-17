#!/usr/bin/env python
"""
Test script for SerpAPI integration in the backend app
"""
import os
import sys
import asyncio
import json
import ssl
import certifi
from dotenv import load_dotenv
import logging

# Add parent directory to path to resolve imports
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, parent_dir)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Import the routers module (this will initialize the serpapi_service singleton)
try:
    from app.routers.outfits import search_product_with_retry, select_best_product
    logger.info("Successfully imported search functions from outfits module")
except ImportError as e:
    logger.error(f"Failed to import search functions: {e}")
    sys.exit(1)

async def test_search():
    """Test the search_product_with_retry function with a simple query"""
    # Load env variables
    load_dotenv()
    
    # Check if API key is set
    api_key = os.environ.get("SERPAPI_API_KEY")
    if not api_key:
        logger.error("No SERPAPI_API_KEY found in environment variables")
        return
    
    masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "***"
    logger.info(f"Using SERPAPI_API_KEY: {masked_key}")
    
    # Test search
    logger.info("Testing product search...")
    
    # Test queries
    test_queries = [
        "blue jeans",
        "white t-shirt",
        "black dress shoes"
    ]
    
    for query in test_queries:
        logger.info(f"Searching for: {query}")
        try:
            result = await search_product_with_retry(query)
            
            if result:
                logger.info(f"✅ Search successful for '{query}'")
                logger.info(f"Product: {result.get('title')} - ${result.get('price')}")
                logger.info(f"Brand: {result.get('brand')}")
                logger.info(f"Image URL: {result.get('image_url')[:60]}...")
            else:
                logger.error(f"❌ No results found for '{query}'")
                
        except Exception as e:
            logger.error(f"❌ Error searching for '{query}': {str(e)}")
    
    logger.info("Search tests completed")

if __name__ == "__main__":
    logger.info("Starting SerpAPI integration test")
    asyncio.run(test_search()) 