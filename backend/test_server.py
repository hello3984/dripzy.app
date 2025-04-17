#!/usr/bin/env python
"""
Test script to verify that the backend server is running and image services are working correctly.
"""
import asyncio
import aiohttp
import argparse
import time
import json
import sys

async def test_server(host="localhost", port=8004):
    """Test if the server is running and responsive"""
    base_url = f"http://{host}:{port}"
    
    print(f"Testing server at {base_url}...")
    
    # Check if server is running
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/") as response:
                if response.status == 200:
                    print(f"✅ Server is running and responding")
                    text = await response.text()
                    print(f"Server response: {text[:100]}...")
                else:
                    print(f"❌ Server responded with status {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Failed to connect to server: {str(e)}")
        return False
    
    # Test outfit generation endpoint with a simple request
    try:
        print("\nTesting outfit generation with a simple request...")
        
        # Use a simple test request that should be fast to process
        test_request = {
            "prompt": "Simple casual outfit",
            "gender": "neutral",
            "budget": 200,
            "style_keywords": ["casual", "simple"]
        }
        
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{base_url}/outfits/generate-test", 
                json=test_request
            ) as response:
                
                elapsed = time.time() - start_time
                print(f"Response received in {elapsed:.2f} seconds")
                
                if response.status == 200:
                    print(f"✅ Test outfit generation succeeded")
                    
                    # Parse response
                    result = await response.json()
                    outfit_count = len(result.get("outfits", []))
                    
                    print(f"Received {outfit_count} outfits")
                    
                    # Check if outfits have collage images
                    collage_count = 0
                    for outfit in result.get("outfits", []):
                        if outfit.get("collage_image"):
                            collage_count += 1
                    
                    print(f"Outfits with collage images: {collage_count}/{outfit_count}")
                    
                    # Print item counts for each outfit
                    print("\nOutfit items breakdown:")
                    for i, outfit in enumerate(result.get("outfits", [])):
                        items = outfit.get("items", [])
                        print(f"  Outfit {i+1}: {len(items)} items")
                        
                        # Count categories
                        categories = {}
                        for item in items:
                            cat = item.get("category", "unknown")
                            if cat in categories:
                                categories[cat] += 1
                            else:
                                categories[cat] = 1
                        
                        # Print category breakdown
                        for cat, count in categories.items():
                            print(f"    - {cat}: {count}")
                else:
                    print(f"❌ Test outfit generation failed with status {response.status}")
                    response_text = await response.text()
                    print(f"Error: {response_text[:500]}")
                    return False
    except Exception as e:
        print(f"❌ Failed to test outfit generation: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test the Fashion AI backend server")
    parser.add_argument("--host", default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=8004, help="Server port")
    
    args = parser.parse_args()
    
    result = asyncio.run(test_server(args.host, args.port))
    
    if result:
        print("\n✨ All tests passed! The server is working correctly.")
        sys.exit(0)
    else:
        print("\n❌ Tests failed. Please check the server logs for errors.")
        sys.exit(1) 