#!/usr/bin/env python
"""
Simple script to test SerpAPI functionality
"""

import os
import sys
import asyncio
import aiohttp
import json
import ssl
import certifi
from dotenv import load_dotenv

# First load environment variables
print("Loading environment variables...")
load_dotenv()

# Get SerpAPI key
serpapi_key = os.environ.get("SERPAPI_API_KEY")

if not serpapi_key:
    print("❌ ERROR: No SERPAPI_API_KEY found in environment variables")
    print("Please add SERPAPI_API_KEY to your .env file")
    sys.exit(1)

masked_key = f"{serpapi_key[:4]}...{serpapi_key[-4:]}" if len(serpapi_key) > 8 else "***"
print(f"✅ SerpAPI key found: {masked_key}")

# Create SSL context
try:
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    print("✅ SSL context created with certifi certificates")
except Exception as e:
    print(f"⚠️ Warning: Could not create SSL context with certifi: {e}")
    print("Will try to use a less secure connection...")
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    print("⚠️ SSL certificate verification disabled for testing")

async def test_serpapi():
    """Test SerpAPI with a simple query"""
    print("\nTesting SerpAPI with a simple query...")
    
    search_params = {
        "q": "blue jeans clothing",
        "tbm": "shop",
        "num": 1,
        "api_key": serpapi_key
    }
    
    try:
        # Make search request with timeout
        timeout = aiohttp.ClientTimeout(total=15)  # 15 seconds total timeout
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        
        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            print("Sending request to SerpAPI...")
            async with session.get(
                "https://serpapi.com/search.json", 
                params=search_params
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    print(f"❌ SerpAPI error: Status {response.status}")
                    print(f"Error details: {error_text[:200]}")
                    return False
                
                try:
                    data = await response.json()
                    
                    if "error" in data:
                        print(f"❌ API error: {data['error']}")
                        return False
                    
                    if "shopping_results" not in data or not data["shopping_results"]:
                        print("❌ No shopping results found")
                        return False
                    
                    # Success - show first result
                    print("\n✅ SerpAPI request successful!")
                    result = data["shopping_results"][0]
                    print(f"\nSample result:")
                    print(f"Title: {result.get('title')}")
                    print(f"Price: {result.get('price')}")
                    print(f"Source: {result.get('source')}")
                    if result.get('thumbnail'):
                        print(f"Image: [Available]")
                    return True
                    
                except json.JSONDecodeError as e:
                    print(f"❌ Failed to parse JSON response: {str(e)}")
                    return False
                
    except aiohttp.ClientError as e:
        print(f"❌ API request error: {str(e)}")
        return False
    except asyncio.TimeoutError:
        print(f"❌ API request timeout after 15 seconds")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    print("\nTesting SerpAPI functionality...")
    result = asyncio.run(test_serpapi())
    
    if result:
        print("\n✅ SerpAPI is working correctly!")
    else:
        print("\n❌ SerpAPI test failed.")
        
    print("\nNote: If the test fails, check:")
    print("1. Your API key is correct")
    print("2. Your internet connection is stable")
    print("3. SerpAPI service is operational (https://serpapi.com/status)") 