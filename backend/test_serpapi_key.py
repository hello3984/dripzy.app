import asyncio
import logging
import os
import sys
from dotenv import load_dotenv

# Configure logging - Make sure we see output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Print debugging info
print("Python version:", sys.version)
print("Current directory:", os.getcwd())

# Load environment variables
print("\nLoading environment variables...")
load_dotenv()
print("Environment variables loaded")

# Print environment variable
serpapi_key = os.getenv("SERPAPI_API_KEY")
print(f"SERPAPI_API_KEY from env: {serpapi_key[:4]}...{serpapi_key[-4:]}" if serpapi_key else "SERPAPI_API_KEY: Not found")
print("All environment variables starting with SERP:")
for key, value in os.environ.items():
    if "SERP" in key:
        masked = value[:4] + "..." + value[-4:] if value and len(value) > 8 else "***"
        print(f"  {key}: {masked}")

print("\nImporting serpapi_service...")
# Import the service (after loading env vars)
try:
    from app.services.serpapi_service import serpapi_service
    print("Successfully imported serpapi_service")
except Exception as e:
    print(f"Error importing serpapi_service: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Check service key
service_key = serpapi_service.api_key
print(f"API key from service: {service_key[:4]}...{service_key[-4:]}" if service_key else "API key from service: Not found")

# Test if key works
async def test_key():
    print("\nTesting API key validity...")
    try:
        # Disable SSL verification for testing
        import ssl
        ssl._create_default_https_context = ssl._create_unverified_context
        print("SSL verification disabled for testing")
        
        is_valid = await serpapi_service.test_api_key()
        print(f"API key is valid: {is_valid}")
        
        if is_valid:
            print("\nTesting search functionality...")
            results = await serpapi_service.search_products(
                query="blue jeans", 
                category="Bottom",
                num_products=1
            )
            if results:
                print(f"Got {len(results)} results")
                print(f"First result: {results[0]}")
                if "fallback" in results[0].get("product_id", ""):
                    print("Using fallback data (API key or rate limit issue)")
                else:
                    print("Got real data from SerpAPI!")
            else:
                print("No results returned")
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()

# Run the test
if __name__ == "__main__":
    print("Running test...")
    asyncio.run(test_key())
    print("Test completed") 