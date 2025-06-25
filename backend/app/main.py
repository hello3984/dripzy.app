from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
import logging
import time
import os
from dotenv import load_dotenv
from datetime import datetime
from contextlib import asynccontextmanager
from pathlib import Path

# Import connection pool manager
from app.core.connection_pool import get_connection_pool
# Import performance monitoring
from app.core.monitoring import performance_monitor

# Import AI router only - temporarily commented out until module path is fixed
# from app.routers.ai import router as ai_router
# Import debug router - temporarily commented out until module path is fixed
# from app.routers.debug import router as debug_router
# Import outfits router
from app.routers.outfits import router as outfits_router
# Import monitoring router
from app.routers.monitoring import router as monitoring_router

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

# CORS configuration
origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3006",
    "http://localhost:3007",
    "https://dripzy.app",
    "http://dripzy.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create metrics directory if it doesn't exist
metrics_path = Path("./metrics")
metrics_path.mkdir(exist_ok=True, parents=True)

# Add Performance Monitoring Middleware
@app.middleware("http")
async def monitoring_middleware(request: Request, call_next):
    start_time = time.time()
    method = request.method
    path = request.url.path
    
    # Log request start
    logger.info(f"Incoming request: {method} {path}")
    
    response = None # Initialize response
    status_code = 500 # Default status code in case of early exit
    
    # Process the request
    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as e:
        logger.error(f"Request failed: {method} {path} - Error: {str(e)}")
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        response = JSONResponse(
            status_code=status_code, 
            content={"detail": f"Middleware Error: {str(e)}"}
        )
    finally:
        # Calculate duration and record metrics
        process_time = time.time() - start_time
        
        # Ensure status_code is set even if call_next failed before assigning response status
        if response is not None:
            status_code = response.status_code 
        
        # Record in performance monitor
        performance_monitor.record_request(
            method=method,
            endpoint=path,
            status_code=status_code,
            duration=process_time,
            metadata={
                "client": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown")
            }
        )
        
        # Log completion
        logger.info(f"Finished request: {method} {path} - Status={status_code} - Time={process_time:.4f}s")
    
    # Ensure a response is always returned
    if response is None:
         # This case should ideally not be reached if the except block handles errors properly
         logger.error(f"Middleware finished without a response object for {method} {path}")
         response = JSONResponse(
             status_code=500, 
             content={"detail": "Internal Server Error in Middleware"}
         )
         
    return response

# Include AI router for modular functionality - temporarily commented out
# app.include_router(ai_router)
# Include debug router - temporarily commented out
# app.include_router(debug_router)
# Include outfits router
app.include_router(outfits_router)
# Include monitoring router
app.include_router(monitoring_router)

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

@app.get("/dashboard")
async def get_monitoring_dashboard():
    """Redirect to the monitoring metrics endpoint."""
    return JSONResponse(content={
        "message": "Performance Monitoring Dashboard", 
        "endpoints": {
            "metrics": "/monitoring/metrics",
            "status": "/monitoring/status",
            "endpoints": "/monitoring/endpoints",
            "slow_requests": "/monitoring/slow-requests"
        }
    })

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
        results = await serpapi_service.search_products(
            query="blue jeans",
            category="Bottom",
            num_results=1
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
            num_results=5
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

# Add test endpoint directly to app
@app.get("/test-collage")
async def test_collage_endpoint():
    """Test endpoint for collage generation"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Testing collage generation")
        
        # Import the real collage_service
        from app.services.collage_service import collage_service
        
        # Use some sample test images
        test_items = [
            {
                "image_url": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=600",
                "category": "Top"
            },
            {
                "image_url": "https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?w=600", 
                "category": "Bottom"
            },
            {
                "image_url": "https://images.unsplash.com/photo-1560343090-f0409e92791a?w=600",
                "category": "Shoes"
            }
        ]
        
        # Test collage service method
        logger.info("Testing collage_service.create_outfit_collage")
        collage_result = collage_service.create_outfit_collage(test_items)
        
        # Return the results for examination
        return {
            "success": True,
            "collage_result": {
                "keys": list(collage_result.keys()) if isinstance(collage_result, dict) else None,
                "image_type": type(collage_result.get("image")).__name__ if isinstance(collage_result, dict) and collage_result.get("image") else None,
                "image_length": len(collage_result.get("image", "")) if isinstance(collage_result, dict) and collage_result.get("image") else 0,
                "image_preview": collage_result.get("image", "")[:50] + "..." if isinstance(collage_result, dict) and collage_result.get("image") else None
            }
        }
    except Exception as e:
        logger.error(f"Error testing collage generation: {str(e)}", exc_info=True)
        return {"success": False, "error": str(e)}

# Add a direct endpoint for /outfits/collage-test to prevent it from matching /{outfit_id}
@app.get("/outfits/collage-test")
async def outfits_collage_test_redirect():
    """Direct endpoint to handle /outfits/collage-test and redirect to /test-collage"""
    return RedirectResponse(url="/test-collage")

# Add after the api_test endpoint
@app.get("/cors-test")
async def cors_test(request: Request):
    """Test endpoint for CORS headers"""
    return {
        "status": "ok",
        "received_headers": dict(request.headers),
        "cors_configured_origins": origins,
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