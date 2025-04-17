#!/usr/bin/env python
"""
Script to analyze SerpAPI responses and build improved matching logic
"""
import os
import sys
import asyncio
import json
import ssl
import certifi
import time
import random
from typing import Dict, List, Any, Optional
from collections import defaultdict
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

# Import the routers module 
try:
    from app.routers.outfits import search_product_with_retry, select_best_product
    logger.info("Successfully imported search functions from outfits module")
except ImportError as e:
    logger.error(f"Failed to import search functions: {e}")
    sys.exit(1)

# Test queries with various attributes
TEST_QUERIES = [
    # Simple queries
    "blue jeans",
    "white t-shirt",
    "black dress shoes",
    # More specific queries
    "nike running shoes",
    "levi's 501 jeans",
    "cashmere sweater",
    # Complex queries
    "red floral summer dress",
    "mens leather casual belt",
    "womens waterproof hiking boots",
    "slim fit business suit"
]

# Different categories to test
CATEGORIES = [
    "Jeans", 
    "T-shirt", 
    "Shoes", 
    "Dress", 
    "Sweater", 
    "Jacket",
    "Pants", 
    "Skirt", 
    "Boots", 
    "Accessories"
]

# Different colors to test
COLORS = [
    "Blue", 
    "Black", 
    "White", 
    "Red", 
    "Green", 
    "Brown", 
    "Grey", 
    "Navy", 
    "Beige", 
    "Pink"
]

# Different search modifiers to test effectiveness
SEARCH_MODIFIERS = [
    " clothing",
    " fashion",
    " apparel",
    " wear",
    ""  # No modifier as control
]

class SerpAPIAnalyzer:
    """Class to analyze SerpAPI results and help optimize search logic"""
    
    def __init__(self):
        self.results = []
        self.category_stats = defaultdict(int)
        self.price_stats = defaultdict(list)
        self.source_stats = defaultdict(int)
        self.modifier_stats = defaultdict(lambda: defaultdict(int))
        self.response_times = []
        
    async def run_analysis(self, iterations=10):
        """Run multiple search iterations and analyze results"""
        # Load env variables
        load_dotenv()
        
        # Check if API key is set
        api_key = os.environ.get("SERPAPI_API_KEY")
        if not api_key:
            logger.error("No SERPAPI_API_KEY found in environment variables")
            return
        
        masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "***"
        logger.info(f"Using SERPAPI_API_KEY: {masked_key}")
        
        # Generate test scenarios
        test_scenarios = self._generate_test_scenarios(iterations)
        logger.info(f"Generated {len(test_scenarios)} test scenarios")
        
        # Run search tests
        for i, scenario in enumerate(test_scenarios):
            logger.info(f"Running test scenario {i+1}/{len(test_scenarios)}")
            await self._run_test_scenario(scenario)
            
            # Add small delay to avoid rate limiting
            await asyncio.sleep(1)
        
        # Analyze results
        self._analyze_results()
    
    def _generate_test_scenarios(self, count):
        """Generate test scenarios with various parameters"""
        scenarios = []
        
        # Add basic query tests
        for query in TEST_QUERIES[:count]:
            scenarios.append({
                "query": query,
                "modifier": " clothing",
                "category": None,
                "color": None
            })
            
        # Add category-specific tests
        for category in CATEGORIES[:min(count, len(CATEGORIES))]:
            scenarios.append({
                "query": f"{category}",
                "modifier": " clothing",
                "category": category,
                "color": None
            })
            
        # Add color + category tests
        for _ in range(min(count, 5)):
            color = random.choice(COLORS)
            category = random.choice(CATEGORIES)
            scenarios.append({
                "query": f"{color} {category}",
                "modifier": " clothing",
                "category": category,
                "color": color
            })
            
        # Add modifier tests
        for modifier in SEARCH_MODIFIERS:
            query = random.choice(TEST_QUERIES)
            scenarios.append({
                "query": query,
                "modifier": modifier,
                "category": None,
                "color": None
            })
            
        return scenarios[:count]  # Limit to requested count
    
    async def _run_test_scenario(self, scenario):
        """Run a single test scenario"""
        query = scenario["query"]
        modifier = scenario["modifier"]
        category = scenario["category"]
        color = scenario["color"]
        
        full_query = query + modifier
        logger.info(f"Searching for: '{full_query}'")
        
        try:
            # Measure response time
            start_time = time.time()
            
            # Override search_product_with_retry to use our modifier
            # This approach preserves the original function's implementation
            async def custom_search():
                """Custom search wrapper to use specific modifier"""
                import aiohttp
                import ssl
                import certifi
                
                # Create SSL context
                try:
                    ssl_context = ssl.create_default_context(cafile=certifi.where())
                except Exception as e:
                    ssl_context = ssl.create_default_context()
                    ssl_context.check_hostname = False
                    ssl_context.verify_mode = ssl.CERT_NONE
                
                # Build search parameters
                search_params = {
                    "q": full_query,
                    "tbm": "shop",
                    "num": 5,
                    "api_key": os.environ.get("SERPAPI_API_KEY"),
                    "tbs": "mr:1",  # Show highly rated items first
                }
                
                # Make search request with timeout
                timeout = aiohttp.ClientTimeout(total=15)
                connector = aiohttp.TCPConnector(ssl=ssl_context)
                
                async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
                    async with session.get(
                        "https://serpapi.com/search.json", 
                        params=search_params
                    ) as response:
                        if response.status != 200:
                            logger.warning(f"API error: Status {response.status}")
                            return None
                        
                        data = await response.json()
                        
                        if "error" in data:
                            logger.error(f"API error: {data['error']}")
                            return None
                        
                        if "shopping_results" not in data or not data["shopping_results"]:
                            return None
                        
                        # Find best matching product from results
                        shopping_results = data["shopping_results"]
                        selected_product = select_best_product(shopping_results, query)
                        
                        if not selected_product:
                            return None
                        
                        # Return full shopping_results and selected product
                        return {
                            "shopping_results": shopping_results,
                            "selected_product": selected_product
                        }
            
            # Run search
            result = await custom_search()
            end_time = time.time()
            response_time = end_time - start_time
            self.response_times.append(response_time)
            
            # Store results
            if result:
                selected_product = result["selected_product"]
                shopping_results = result["shopping_results"]
                
                success = True
                product_title = selected_product.get("title", "")
                product_price = selected_product.get("price", "")
                product_source = selected_product.get("source", "")
                results_count = len(shopping_results)
                
                logger.info(f"✅ Found {results_count} results in {response_time:.2f}s")
                logger.info(f"   Selected: {product_title} - {product_price}")
                
                # Update statistics
                source = product_source.split()[0] if product_source else "Unknown"
                self.source_stats[source] += 1
                
                if category:
                    self.category_stats[category] += 1
                
                try:
                    # Extract numeric price
                    price_str = product_price.replace("$", "").replace(",", "")
                    price = float(price_str)
                    self.price_stats[category or "general"].append(price)
                except:
                    pass
                
                self.modifier_stats[modifier]["success"] += 1
                self.modifier_stats[modifier]["count"] += 1
                
            else:
                success = False
                logger.warning(f"❌ No results for '{full_query}' after {response_time:.2f}s")
                self.modifier_stats[modifier]["count"] += 1
            
            # Record result
            self.results.append({
                "query": query,
                "full_query": full_query,
                "category": category,
                "color": color,
                "modifier": modifier,
                "success": success,
                "response_time": response_time,
                "selected_product": result["selected_product"] if result else None,
                "results_count": len(result["shopping_results"]) if result else 0
            })
            
        except Exception as e:
            logger.error(f"❌ Error processing '{full_query}': {str(e)}")
            self.results.append({
                "query": query,
                "full_query": full_query,
                "category": category,
                "color": color,
                "modifier": modifier,
                "success": False,
                "error": str(e)
            })
    
    def _analyze_results(self):
        """Analyze collected results and generate insights"""
        total_searches = len(self.results)
        successful_searches = sum(1 for r in self.results if r.get("success", False))
        success_rate = (successful_searches / total_searches) * 100 if total_searches > 0 else 0
        
        avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        
        logger.info("\n==== ANALYSIS RESULTS ====")
        logger.info(f"Total searches: {total_searches}")
        logger.info(f"Successful searches: {successful_searches} ({success_rate:.1f}%)")
        logger.info(f"Average response time: {avg_response_time:.2f}s")
        
        # Analyze search modifiers
        logger.info("\nSearch modifier effectiveness:")
        for modifier, stats in self.modifier_stats.items():
            success_count = stats.get("success", 0)
            total_count = stats.get("count", 0)
            success_rate = (success_count / total_count) * 100 if total_count > 0 else 0
            logger.info(f"  Modifier '{modifier}': {success_rate:.1f}% success ({success_count}/{total_count})")
        
        # Analyze popular sources
        logger.info("\nPopular product sources:")
        for source, count in sorted(self.source_stats.items(), key=lambda x: x[1], reverse=True)[:5]:
            logger.info(f"  {source}: {count} products")
        
        # Analyze price ranges
        logger.info("\nPrice statistics by category:")
        for category, prices in self.price_stats.items():
            if prices:
                avg_price = sum(prices) / len(prices)
                min_price = min(prices)
                max_price = max(prices)
                logger.info(f"  {category}: avg=${avg_price:.2f}, range=${min_price:.2f}-${max_price:.2f}")
        
        # Generate recommendations
        self._generate_recommendations()
    
    def _generate_recommendations(self):
        """Generate recommendations for search optimization"""
        # Find best modifier
        best_modifier = None
        best_success_rate = 0
        
        for modifier, stats in self.modifier_stats.items():
            success_count = stats.get("success", 0)
            total_count = stats.get("count", 0)
            if total_count > 0:
                success_rate = (success_count / total_count) * 100
                if success_rate > best_success_rate:
                    best_success_rate = success_rate
                    best_modifier = modifier
        
        # Find fastest modifier
        modifier_times = defaultdict(list)
        for result in self.results:
            if "response_time" in result:
                modifier_times[result["modifier"]].append(result["response_time"])
        
        fastest_modifier = None
        fastest_time = float('inf')
        
        for modifier, times in modifier_times.items():
            if times:
                avg_time = sum(times) / len(times)
                if avg_time < fastest_time:
                    fastest_time = avg_time
                    fastest_modifier = modifier
        
        logger.info("\n==== RECOMMENDATIONS ====")
        
        if best_modifier is not None:
            logger.info(f"Most successful search modifier: '{best_modifier}' ({best_success_rate:.1f}% success)")
        
        if fastest_modifier is not None:
            logger.info(f"Fastest search modifier: '{fastest_modifier}' ({fastest_time:.2f}s avg)")
        
        # Recommend optimal search approach based on analysis
        logger.info("\nRecommended search approach:")
        
        # Generate specific recommendations
        recommendations = []
        
        if best_modifier is not None:
            recommendations.append(f"1. Use '{best_modifier}' as the primary search modifier for highest success rate")
        
        # Look at which categories have the best success
        successful_categories = {}
        for result in self.results:
            if result.get("success", False) and result.get("category"):
                category = result["category"]
                successful_categories[category] = successful_categories.get(category, 0) + 1
        
        if successful_categories:
            best_categories = sorted(successful_categories.items(), key=lambda x: x[1], reverse=True)[:3]
            categories_str = ", ".join([f"'{c}'" for c, _ in best_categories])
            recommendations.append(f"2. Category terms {categories_str} had the highest success rates")
        
        # Check if color specification helps
        color_success = 0
        color_total = 0
        no_color_success = 0
        no_color_total = 0
        
        for result in self.results:
            if result.get("color"):
                color_total += 1
                if result.get("success", False):
                    color_success += 1
            else:
                no_color_total += 1
                if result.get("success", False):
                    no_color_success += 1
        
        color_rate = (color_success / color_total) * 100 if color_total > 0 else 0
        no_color_rate = (no_color_success / no_color_total) * 100 if no_color_total > 0 else 0
        
        if color_rate > no_color_rate:
            recommendations.append(f"3. Including color terms improves search success ({color_rate:.1f}% vs {no_color_rate:.1f}%)")
        else:
            recommendations.append(f"3. Color terms did not significantly improve searches ({color_rate:.1f}% vs {no_color_rate:.1f}%)")
        
        for i, recommendation in enumerate(recommendations):
            logger.info(f"  {recommendation}")
        
        # Save results to file
        self._save_results()
    
    def _save_results(self):
        """Save analysis results to file"""
        output_file = os.path.join(os.path.dirname(__file__), "serpapi_analysis.json")
        
        output_data = {
            "summary": {
                "total_searches": len(self.results),
                "successful_searches": sum(1 for r in self.results if r.get("success", False)),
                "avg_response_time": sum(self.response_times) / len(self.response_times) if self.response_times else 0
            },
            "modifier_stats": dict(self.modifier_stats),
            "source_stats": dict(self.source_stats),
            "results": self.results
        }
        
        try:
            with open(output_file, "w") as f:
                json.dump(output_data, f, indent=2)
            logger.info(f"\nAnalysis results saved to: {output_file}")
        except Exception as e:
            logger.error(f"Failed to save results: {e}")

async def main():
    """Run the SerpAPI analyzer"""
    logger.info("Starting SerpAPI analysis")
    analyzer = SerpAPIAnalyzer()
    await analyzer.run_analysis(iterations=10)

if __name__ == "__main__":
    asyncio.run(main()) 