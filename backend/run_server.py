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
import certifi

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

def create_ssl_context():
    """Create a default SSL context with proper certificate verification"""
    try:
        # Create default context using certifi for certificate verification
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        logger.info("Created default SSL context with certifi certificates")
        return ssl_context
    except Exception as e:
        logger.error(f"Error creating SSL context: {str(e)}")
        # Fallback to default context
        return ssl.create_default_context()

def parse_args():
    parser = argparse.ArgumentParser(description="Run the FastAPI server")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
    parser.add_argument("--reload", dest="reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--no-reload", dest="reload", action="store_false", help="Disable auto-reload")
    parser.add_argument("--stable", action="store_true", help="Run in stable mode (no reload, production-like)")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")
    parser.set_defaults(reload=True)
    return parser.parse_args()

def main():
    # Parse command line arguments
    args = parse_args()
    
    # Set port
    port = args.port
    
    # Set reload flag (default to False for stability)
    reload_enabled = args.reload and not args.stable
    
    logger.info(f"Starting server on port {port} with reload={'enabled' if reload_enabled else 'disabled'}...")
    
    # Set OpenSSL environment variables to allow insecure connections
    os.environ["PYTHONHTTPSVERIFY"] = "0"  # Disable HTTPS verification
    
    # Create and set default SSL context
    ssl_context = create_ssl_context()
    # Set the default SSL context for all HTTPS requests
    ssl._create_default_https_context = lambda: ssl_context
    logger.info("Created default SSL context for application")
    
    # Check if .watchexclude file exists and use it
    exclude_file = os.path.join(os.path.dirname(__file__), ".watchexclude")
    reload_dirs = ["app"]  # Only watch the app directory by default
    
    # Run uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=reload_enabled,
        reload_dirs=reload_dirs if reload_enabled else None,
        reload_excludes=["tests/*", "test_*", "__pycache__/*", "*.pyc"] if reload_enabled else None,
        ssl_keyfile=None,
        ssl_certfile=None,
        log_level="info",
        workers=args.workers
    )

if __name__ == "__main__":
    main() 