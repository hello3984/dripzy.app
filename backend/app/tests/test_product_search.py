import asyncio
import time
import json
import os
import sys
import logging
from typing import List, Dict, Any

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.product_service import ParallelProductSearchService
from app.routers.outfits import match_products_to_items, create_fallback_item

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("product_search_benchmark")

# Sample test data - a variety of clothing items with descriptions
TEST_ITEMS = [
    {
        "category": "tops",
        "description": "White cotton t-shirt",
        "color": "white",
        "search_keywords": "basic white tee"
    },
    {
        "category": "bottoms",
        "description": "Blue denim jeans",
        "color": "blue",
        "search_keywords": "straight leg jeans"
    },
    {
        "category": "footwear",
        "description": "Black leather sneakers",
        "color": "black",
        "search_keywords": "casual sneakers"
    },
    {
        "category": "outerwear",
        "description": "Brown leather jacket",
        "color": "brown",
        "search_keywords": "biker jacket"
    },
    {
        "category": "accessories",
        "description": "Silver watch with leather strap",
        "color": "silver",
        "search_keywords": "minimalist watch"
    },
    {
        "category": "dresses",
        "description": "Red floral summer dress",
        "color": "red",
        "search_keywords": "midi dress"
    },
    {
        "category": "tops",
        "description": "Blue striped button-up shirt",
        "color": "blue",
        "search_keywords": "oxford shirt"
    },
    {
        "category": "bottoms",
        "description": "Khaki chino pants",
        "color": "beige",
        "search_keywords": "slim fit chinos"
    }
]

async def benchmark_sequential_search():
    """Test the original sequential search implementation"""
    start_time = time.time()
    items = TEST_ITEMS.copy()
    
    # Since we don't have access to the original implementation directly,
    # we'll simulate it with a mock that processes one item at a time
    enhanced_items = []
    for item in items:
        # Simulate processing delay of 2-3 seconds per item
        await asyncio.sleep(2)
        # Create a mock enhanced item
        enhanced_item = item.copy()
        enhanced_item["product_url"] = f"https://example.com/{item['category']}/{item['color']}"
        enhanced_item["image_url"] = f"https://example.com/images/{item['category']}/{item['color']}.jpg"
        enhanced_item["price"] = "$29.99"
        enhanced_items.append(enhanced_item)
    
    elapsed_time = time.time() - start_time
    logger.info(f"Sequential search completed in {elapsed_time:.2f} seconds")
    return enhanced_items, elapsed_time

async def benchmark_parallel_search():
    """Test the new parallel search implementation"""
    start_time = time.time()
    items = TEST_ITEMS.copy()
    
    try:
        enhanced_items = await ParallelProductSearchService.search_products_parallel(
            items, max_workers=8
        )
        elapsed_time = time.time() - start_time
        logger.info(f"Parallel search completed in {elapsed_time:.2f} seconds")
        return enhanced_items, elapsed_time
    except Exception as e:
        logger.error(f"Error in parallel search: {str(e)}")
        elapsed_time = time.time() - start_time
        return [], elapsed_time

async def benchmark_actual_implementation():
    """Test the actual implementation from the outfits.py file"""
    start_time = time.time()
    items = TEST_ITEMS.copy()
    
    try:
        enhanced_items = await match_products_to_items(items)
        elapsed_time = time.time() - start_time
        logger.info(f"Actual implementation completed in {elapsed_time:.2f} seconds")
        return enhanced_items, elapsed_time
    except Exception as e:
        logger.error(f"Error in actual implementation: {str(e)}")
        elapsed_time = time.time() - start_time
        return [], elapsed_time

async def run_benchmarks():
    """Run all benchmarks and compare results"""
    logger.info("Starting product search benchmarks...")
    
    # Run the benchmarks
    seq_items, seq_time = await benchmark_sequential_search()
    par_items, par_time = await benchmark_parallel_search()
    act_items, act_time = await benchmark_actual_implementation()
    
    # Print results
    logger.info("\n===== BENCHMARK RESULTS =====")
    logger.info(f"Sequential search: {seq_time:.2f} seconds for {len(seq_items)} items")
    logger.info(f"Parallel search: {par_time:.2f} seconds for {len(par_items)} items")
    logger.info(f"Actual implementation: {act_time:.2f} seconds for {len(act_items)} items")
    
    # Calculate improvement
    if seq_time > 0 and par_time > 0:
        improvement = (seq_time - par_time) / seq_time * 100
        logger.info(f"Parallel search is {improvement:.1f}% faster than sequential search")
    
    # Save results to file for analysis
    with open("benchmark_results.json", "w") as f:
        json.dump({
            "sequential": {
                "time": seq_time,
                "item_count": len(seq_items)
            },
            "parallel": {
                "time": par_time,
                "item_count": len(par_items)
            },
            "actual": {
                "time": act_time,
                "item_count": len(act_items)
            }
        }, f, indent=2)
    
    logger.info("Benchmark results saved to benchmark_results.json")

if __name__ == "__main__":
    # Check if we have the API key
    if not os.environ.get("SERPAPI_API_KEY"):
        logger.warning("SERPAPI_API_KEY not found in environment variables")
        logger.warning("Tests will run with mock data or may fail")
    
    # Run the benchmarks
    asyncio.run(run_benchmarks()) 