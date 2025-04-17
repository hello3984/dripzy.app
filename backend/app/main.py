from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import time
import os
from dotenv import load_dotenv
from datetime import datetime
from contextlib import asynccontextmanager

# Import connection pool manager
from app.core.connection_pool import get_connection_pool

# Import AI router only - temporarily commented out until module path is fixed
# from app.routers.ai import router as ai_router
# Import debug router - temporarily commented out until module path is fixed
# from app.routers.debug import router as debug_router
# Import outfits router
from app.routers.outfits import router as outfits_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Define application lifespan for resource management
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize resources
    logger.info("Starting application and initializing connection pools")
    pool_manager = get_connection_pool()
    
    # Initialize any connection pools we'll need
    await pool_manager.get_client("serpapi")
    await pool_manager.get_client("anthropic", timeout=60.0)
    
    yield
    
    # Shutdown: cleanup resources
    logger.info("Application shutting down, cleaning up resources")
    await pool_manager.close_all()

app = FastAPI(
    title="Dripzy Fashion AI API",
    description="API for the Dripzy fashion AI recommendation platform",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://dripzy.app", "http://localhost:3000", "http://localhost:5173", "http://localhost:3006"],  # Added localhost:3006
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Only methods you use
    allow_headers=["Authorization", "Content-Type", "DeviceID", "User-Agent"],  # Only headers you need
    max_age=600  # Cache preflight requests for 10 minutes
)

# Add Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.info(f"Incoming request: {request.method} {request.url.path}")
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"Finished request: {request.method} {request.url.path} - Status={response.status_code} - Time={process_time:.4f}s")
    return response

# Include AI router for modular functionality - temporarily commented out
# app.include_router(ai_router)
# Include debug router - temporarily commented out
# app.include_router(debug_router)
# Include outfits router
app.include_router(outfits_router)

# Handle OPTIONS requests for CORS preflight
@app.options("/{rest_of_path:path}")
async def options_handler(rest_of_path: str):
    return {}


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"An unexpected error occurred: {str(exc)}"},
    )

@app.get("/")
async def root():
    return {"message": "Welcome to the Dripzy Fashion AI API. Visit /docs for API documentation."}

@app.get("/health")
async def health_check():
    """Health check endpoint for the API."""
    try:
        # Check environment variables
        api_keys = {
            "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY") is not None,
            "SERPAPI_API_KEY": os.getenv("SERPAPI_API_KEY") is not None,
        }
        
        # Return health status
        return {
            "status": "healthy",
            "api_keys": api_keys,
            "version": "0.1.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "unhealthy", "error": str(e)}
        )

@app.get("/debug-serpapi")
async def debug_serpapi_direct():
    """Direct debug endpoint for SerpAPI configuration and account status"""
    import os
    from dotenv import load_dotenv
    from app.services.serpapi_service import serpapi_service
    import requests
    
    # Try to reload environment variables
    load_dotenv()
    
    # Check if SERPAPI_API_KEY is in environment variables
    serpapi_key = os.getenv("SERPAPI_API_KEY")
    masked_key = serpapi_key[:4] + "..." + serpapi_key[-4:] if serpapi_key and len(serpapi_key) > 8 else None
    
    # Get the service's API key
    service_key = serpapi_service.api_key
    masked_service_key = service_key[:4] + "..." + service_key[-4:] if service_key and len(service_key) > 8 else None
    
    # Check SerpAPI account status directly
    account_info = {}
    try:
        account_url = "https://serpapi.com/account"
        response = requests.get(account_url, params={"api_key": service_key})
        if response.status_code == 200:
            account_info = response.json()
        else:
            account_info = {"error": f"Failed to get account info: Status {response.status_code}"}
    except Exception as e:
        account_info = {"error": f"Error checking account: {str(e)}"}
    
    # Test a search to see if we get fallback data due to rate limits
    try:
        results = serpapi_service.search_products(
            query="blue jeans",
            category="Bottom",
            gender="unisex",
            limit=1
        )
        first_result = results[0] if results else None
        is_fallback = "fallback" in first_result.get("product_id", "") if first_result else True
        fallback_reason = first_result.get("fallback_reason", "Unknown") if is_fallback else None
    except Exception as e:
        first_result = {"error": str(e)}
        is_fallback = True
        fallback_reason = str(e)
    
    # Check if we're out of API calls
    out_of_searches = False
    account_status = account_info.get("account_status", "")
    if "run out of searches" in account_status:
        out_of_searches = True
    
    return {
        "environment_key": masked_key is not None,
        "environment_key_value": masked_key,
        "service_key": masked_service_key is not None,
        "service_key_value": masked_service_key,
        "account_info": {
            "plan": account_info.get("plan_name", "Unknown"),
            "status": account_info.get("account_status", "Unknown"),
            "searches_per_month": account_info.get("searches_per_month", 0),
            "this_month_usage": account_info.get("this_month_usage", 0),
            "searches_left": account_info.get("total_searches_left", 0),
            "out_of_searches": out_of_searches
        },
        "test_result": {
            "is_fallback": is_fallback,
            "fallback_reason": fallback_reason,
            "product": first_result
        }
    }

@app.get("/test-serpapi")
async def test_serpapi_direct(query: str = "winter jacket", category: str = "Top", gender: str = "male"):
    """Direct test endpoint for SerpAPI product search"""
    from app.services.serpapi_service import serpapi_service
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Testing SerpAPI search for: {query} in category {category}")
        products = await serpapi_service.search_products(
            query=query,
            category=category,
            gender=gender,
            limit=5
        )
        return {"products": products, "count": len(products)}
    except Exception as e:
        logger.error(f"Error testing SerpAPI: {str(e)}", exc_info=True)
        return {"error": str(e)}

# Add a very simple debug endpoint to test API is working
@app.get("/api-test")
async def api_test():
    """Simple API test without any dependencies"""
    return {
        "status": "ok",
        "message": "API is working correctly",
        "timestamp": str(datetime.now())
    }

# Run with: uvicorn app.main:app --reload
if __name__ == "__main__":
    import uvicorn
    import socket
    import sys
    
    # Check if the port is already in use
    port = 8000
    try:
        # Try to create a socket with the port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('127.0.0.1', port))
        sock.close()
    except socket.error:
        print(f"WARNING: Port {port} is already in use!")
        # Try to find another open port
        for alt_port in range(8001, 8020):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.bind(('127.0.0.1', alt_port))
                sock.close()
                port = alt_port
                print(f"Using alternative port: {port}")
                break
            except socket.error:
                continue
        else:
            print("ERROR: Could not find an open port between 8000-8019. Server cannot start.")
            sys.exit(1)
    
    # Start the server with the determined port
    print(f"Starting server on port {port}")
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True) 