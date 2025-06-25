import asyncio
import httpx
import json
import time
import os
from dotenv import load_dotenv

# Load environment variables from .env file in the root
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=dotenv_path)

# --- Configuration ---
BACKEND_URL = "http://localhost:8000"
# Adjust timeout as needed (seconds) - give it ample time for LLM + SerpApi
REQUEST_TIMEOUT = 300.0 # 5 minutes

# --- Test Data --- 
# Modify this dictionary to test different prompts
test_request_data = {
    "prompt": "Beach Vacation outfit",
    "gender": "female",
    "budget": 500,
    "include_alternatives": True,
    "occasion": "vacation" # Example, adjust as needed
}
# -------------------

async def run_generation_test():
    """Runs the outfit generation test against the backend API."""
    target_url = f"{BACKEND_URL}/outfits/generate"
    print(f"--- Testing Outfit Generation ---")
    print(f"Target URL: {target_url}")
    print(f"Request Data:")
    print(json.dumps(test_request_data, indent=2))
    print(f"Timeout set to: {REQUEST_TIMEOUT} seconds")
    print("-----------------------------------")
    print("Sending request...")

    start_time = time.time()
    response_data = None
    status_code = None
    error_message = None

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.post(
                target_url, 
                json=test_request_data
            )
            status_code = response.status_code
            response.raise_for_status() # Raise HTTPStatusError for bad responses (4xx or 5xx)
            response_data = response.json()
            
    except httpx.HTTPStatusError as e:
        error_message = f"HTTP Error: {e.response.status_code}"
        try:
            response_data = e.response.json() 
        except json.JSONDecodeError:
            response_data = {"error_detail": e.response.text[:500]} # Show partial text
    except httpx.TimeoutException:
        error_message = f"Request timed out after {REQUEST_TIMEOUT} seconds."
    except httpx.RequestError as e:
        error_message = f"Request failed: Could not connect to {e.request.url}. Is the backend running?"
    except json.JSONDecodeError as e:
        error_message = f"Failed to decode JSON response: {e}"
    except Exception as e:
        error_message = f"An unexpected error occurred: {e}"

    end_time = time.time()
    duration = end_time - start_time

    print(f"--- Results ({duration:.2f}s) ---")
    print(f"Status Code: {status_code}")

    if error_message:
        print(f"Error: {error_message}")
    
    if response_data:
        print("Response JSON:")
        print(json.dumps(response_data, indent=2))
    else:
        print("No JSON response received.")
    print("---------------------------")

if __name__ == "__main__":
    print("Ensure backend server is running on port 8000...")
    time.sleep(1)
    asyncio.run(run_generation_test()) 