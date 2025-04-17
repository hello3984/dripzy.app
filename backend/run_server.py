#!/usr/bin/env python
"""
Run the FastAPI server with proper settings.
This script handles SSL certificate issues and sets up logging.
"""

import os
import sys
import logging
import ssl
import uvicorn
import argparse
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Print environment variables for debugging
serpapi_key = os.getenv("SERPAPI_API_KEY")
logger.info(f"SERPAPI_API_KEY: {'Present' if serpapi_key else 'Not found'}")
if serpapi_key:
    masked_key = serpapi_key[:4] + "..." + serpapi_key[-4:] if len(serpapi_key) > 8 else "***"
    logger.info(f"Key value: {masked_key}")

# Create a custom SSL context to resolve SSL issues
try:
    ssl_context = ssl.create_default_context()
    logger.info("Created default SSL context")
except Exception as e:
    logger.warning(f"Could not create default SSL context: {e}")
    ssl_context = ssl._create_unverified_context()
    logger.warning("Using unverified SSL context")

def parse_args():
    parser = argparse.ArgumentParser(description="Run the FastAPI server")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
    parser.add_argument("--reload", dest="reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--no-reload", dest="reload", action="store_false", help="Disable auto-reload")
    parser.set_defaults(reload=True)
    return parser.parse_args()

# Run the server
if __name__ == "__main__":
    # Parse command line arguments
    args = parse_args()
    
    # Set port
    port = args.port
    
    # Set reload flag (default to False for stability)
    reload_enabled = args.reload
    
    logger.info(f"Starting server on port {port} with reload={'enabled' if reload_enabled else 'disabled'}...")
    
    # Set OpenSSL environment variables to allow insecure connections
    os.environ["PYTHONHTTPSVERIFY"] = "0"  # Disable HTTPS verification
    
    # Run uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=reload_enabled,
        ssl_keyfile=None,
        ssl_certfile=None,
        log_level="info"
    ) 