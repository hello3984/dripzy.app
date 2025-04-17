"""
Debug router for internal development and testing purposes.
"""

import logging
import os
from typing import Dict, Any, List

from fastapi import APIRouter, HTTPException
from dotenv import load_dotenv

from app.services.serpapi_service import serpapi_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/debug", tags=["debug"], include_in_schema=False)

@router.get("/serpapi")
async def debug_serpapi():
    """Debug endpoint to check SerpAPI configuration"""
    # Try to reload environment variables
    load_dotenv()
    
    # Check if SERPAPI_KEY is in environment variables
    serpapi_key = os.getenv("SERPAPI_KEY")
    masked_key = serpapi_key[:4] + "..." + serpapi_key[-4:] if serpapi_key and len(serpapi_key) > 8 else None
    
    # Check if the key exists in a secret file
    secret_file_exists = os.path.exists("/etc/secrets/SERPAPI_KEY")
    secret_file_content = None
    if secret_file_exists:
        try:
            with open("/etc/secrets/SERPAPI_KEY", "r") as f:
                secret_content = f.read().strip()
                secret_file_content = secret_content[:4] + "..." + secret_content[-4:] if len(secret_content) > 8 else "***"
        except Exception as e:
            secret_file_content = f"Error reading: {str(e)}"
    
    # Get the service's API key
    service_key = serpapi_service.api_key
    masked_service_key = service_key[:4] + "..." + service_key[-4:] if service_key and len(service_key) > 8 else None
    
    # Test a real API call
    try:
        results = serpapi_service.search_products(
            query="blue jeans",
            category="Bottom",
            gender="unisex",
            limit=1
        )
        api_working = not any("fallback" in result.get("product_id", "") for result in results)
        first_result = results[0] if results else None
        is_fallback = "fallback" in first_result.get("product_id", "") if first_result else True
    except Exception as e:
        api_working = False
        first_result = str(e)
        is_fallback = True
    
    return {
        "environment_key": masked_key is not None,
        "environment_key_value": masked_key,
        "secret_file_exists": secret_file_exists,
        "secret_file_content": secret_file_content,
        "service_key": masked_service_key is not None,
        "service_key_value": masked_service_key,
        "api_working": api_working,
        "is_fallback": is_fallback,
        "first_result_type": type(first_result).__name__,
        "first_result": {k: v for k, v in first_result.items()} if isinstance(first_result, dict) else str(first_result)
    }

@router.get("/test-serpapi")
async def test_serpapi(query: str = "blue jeans", category: str = "Bottom", gender: str = "unisex"):
    """Test endpoint for SerpAPI product search"""
    try:
        logger.info(f"Testing SerpAPI search for: {query} in category {category}")
        products = serpapi_service.search_products(
            query=query,
            category=category,
            gender=gender,
            limit=5
        )
        return {"products": products, "count": len(products)}
    except Exception as e:
        logger.error(f"Error testing SerpAPI: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error testing SerpAPI: {str(e)}") 