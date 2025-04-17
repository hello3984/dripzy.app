#!/usr/bin/env python
"""
Test script to directly test the match_products_to_items function with mock data
"""
import asyncio
import json
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.abspath("."))

# Force using mock data
os.environ["USE_MOCK_DATA"] = "true"
os.environ["MOCK_API_RESPONSE"] = "true"
os.environ["SERPAPI_API_KEY"] = ""  # Empty key forces mock data

async def test_product_matching():
    """Test the match_products_to_items function directly using mock data"""
    try:
        # Import the function directly from the module
        from app.routers.outfits import match_products_to_items
        from app.utils.search_utils import create_mock_product_data
        
        print("Successfully imported match_products_to_items function")
        
        # Create test item data
        test_items = [
            {
                "description": "Blue jeans with straight leg",
                "category": "Bottom",
                "color": "Blue",
                "search_keywords": ["jeans", "denim", "pants"]
            },
            {
                "description": "White cotton t-shirt",
                "category": "Top",
                "color": "White",
                "search_keywords": ["t-shirt", "tee", "casual"]
            },
            {
                "description": "Black leather boots",
                "category": "Shoes",
                "color": "Black",
                "search_keywords": ["boots", "leather", "footwear"]
            }
        ]
        
        print(f"Testing with {len(test_items)} items")
        
        # Patch the search_product function to directly use mock data
        from app.utils import search_utils
        original_search_product = search_utils.search_product
        
        async def mock_search_product(query: str):
            print(f"Using mock data for query: {query}")
            return create_mock_product_data(query)
            
        # Replace the function temporarily
        search_utils.search_product = mock_search_product
        
        try:
            # Call the function directly
            enhanced_items = await match_products_to_items(test_items)
            
            print(f"Function returned {len(enhanced_items)} enhanced items")
            
            # Print the results
            for i, item in enumerate(enhanced_items):
                print(f"\nItem {i+1}: {item.get('description')}")
                print(f"  Category: {item.get('category')}")
                
                # Check all possible field names for Product URL
                product_url = item.get('product_url') or item.get('url') or item.get('link') or "Not found"
                print(f"  Product URL: {product_url}")
                
                # Check all possible field names for Image URL
                image_url = item.get('image_url') or item.get('thumbnail') or "Not found"
                print(f"  Image URL: {image_url}")
                
                # Check price field (also check if it's a number or string)
                price = item.get('price')
                if price is not None:
                    price_str = f"${price}" if isinstance(price, (int, float)) else price
                    print(f"  Price: {price_str}")
                else:
                    print(f"  Price: Not found")
                
                # Check if this is a fallback item
                print(f"  Is Fallback: {item.get('is_fallback', False)}")
                
                # Print any title or brand information if available
                if 'title' in item:
                    print(f"  Title: {item['title']}")
                if 'brand' in item:
                    print(f"  Brand: {item['brand']}")
        finally:
            # Restore the original function
            search_utils.search_product = original_search_product
        
        return True
        
    except ImportError as e:
        print(f"Error importing function: {str(e)}")
        return False
    except Exception as e:
        print(f"Error during product matching test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_product_matching())
    
    if result:
        print("\n✅ Product matching test completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Product matching test failed.")
        sys.exit(1) 