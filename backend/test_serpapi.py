import os
import sys
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the parent directory to the path so we can import the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Print all environment variables for debugging
logger.info("Environment variables:")
for key in os.environ:
    if key.startswith("SERPAPI") or key.startswith("ANTHROPIC"):
        # Mask the value for security
        value = os.environ[key]
        masked_value = value[:4] + "..." + value[-4:] if len(value) > 8 else "***"
        logger.info(f"  {key}: {masked_value}")

# Try to import and use the SerpAPI service
try:
    from app.services.serpapi_service import serpapi_service
    
    logger.info("Testing SerpAPI search...")
    
    # Test search with a simple query
    results = serpapi_service.search_products(
        query="blue jeans",
        category="Bottom",
        gender="unisex",
        limit=2
    )
    
    logger.info(f"Search returned {len(results)} results")
    
    # Check if results are real or fallback
    if results and len(results) > 0:
        if "fallback" in results[0]["product_id"]:
            logger.error("Got fallback results - SerpAPI not working!")
            logger.info(f"First result: {results[0]}")
        else:
            logger.info("Got real results from SerpAPI!")
            for i, result in enumerate(results):
                logger.info(f"Result {i+1}:")
                logger.info(f"  Product: {result['product_name']}")
                logger.info(f"  Brand: {result['brand']}")
                logger.info(f"  Price: ${result['price']}")
                logger.info(f"  Image: {result['image_url'][:30]}...")
    else:
        logger.error("No results returned")
        
except Exception as e:
    logger.error(f"Error: {e}")
    raise 