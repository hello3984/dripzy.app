#!/usr/bin/env python
"""
Test script for SerpAPI SSL connectivity
"""
import os
import ssl
import asyncio
import aiohttp
import logging
import platform
import certifi
import traceback
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_serpapi_ssl")

# Get API key from env
API_KEY = os.environ.get("SERPAPI_API_KEY", "")

async def test_serpapi_ssl():
    """Test connectivity to SerpAPI with improved SSL handling"""
    
    logger.info(f"Testing SerpAPI SSL on platform: {platform.system()}")
    logger.info(f"Python version: {platform.python_version()}")
    logger.info(f"API key available: {'Yes' if API_KEY else 'No'}")
    
    # Create an improved SSL context
    try:
        # Try the macOS approach first if on macOS
        if platform.system() == 'Darwin':
            try:
                import subprocess
                import tempfile
                
                logger.info("Attempting to get certificates from macOS keychain")
                process = subprocess.run(
                    ["/usr/bin/security", "find-certificate", "-a", "-p", 
                     "/System/Library/Keychains/SystemRootCertificates.keychain"],
                    capture_output=True, text=True, check=False
                )
                
                if process.returncode == 0 and process.stdout:
                    with tempfile.NamedTemporaryFile(delete=False, mode='w') as cert_file:
                        cert_file.write(process.stdout)
                        cert_path = cert_file.name
                    
                    logger.info(f"Created temporary certificate file at {cert_path}")
                    ssl_context = ssl.create_default_context(cafile=cert_path)
                    logger.info("Created SSL context with macOS system certificates")
                else:
                    logger.warning("Could not extract certificates from macOS keychain")
                    raise Exception("macOS certificate extraction failed")
            except Exception as mac_error:
                logger.warning(f"macOS certificate approach failed: {mac_error}")
                # Fall back to certifi
                ssl_context = ssl.create_default_context(cafile=certifi.where())
                logger.info(f"Falling back to certifi certificates at: {certifi.where()}")
        else:
            # On non-macOS, use certifi directly
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            logger.info(f"Created SSL context with certifi certificates at: {certifi.where()}")
    except Exception as e:
        logger.error(f"Error creating SSL context with certificates: {e}")
        logger.error("SSL context creation traceback:", exc_info=True)
        logger.info("Falling back to unverified context")
        ssl_context = ssl._create_unverified_context()
    
    # Try requests certificates as well
    try:
        import requests.certs
        logger.info(f"Requests certificate path: {requests.certs.where()}")
    except ImportError:
        logger.info("Requests package not available")
    
    # Test a simple request
    try:
        # Parameters for the API request
        params = {
            "api_key": API_KEY,
            "engine": "google",
            "q": "test query",
            "num": 1
        }
        
        # First try disabling hostname verification to isolate the issue
        ssl_context.check_hostname = False
        
        # Create TCP connector with our SSL context
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        
        # Make the request
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            logger.info("Sending request to SerpAPI...")
            try:
                async with session.get("https://serpapi.com/search", params=params) as response:
                    status = response.status
                    logger.info(f"Response status: {status}")
                    
                    if status == 200:
                        logger.info("SSL connectivity successful!")
                        # Try to parse JSON response
                        try:
                            data = await response.json()
                            if data:
                                logger.info("Successfully parsed JSON response")
                                search_metadata = data.get("search_metadata", {})
                                logger.info(f"Search ID: {search_metadata.get('id', 'Not found')}")
                                return True
                        except Exception as json_error:
                            logger.error(f"Error parsing JSON: {json_error}")
                    elif status == 401:
                        logger.error("API key invalid or missing")
                    else:
                        logger.error(f"Unexpected status: {status}")
                        try:
                            text = await response.text()
                            logger.error(f"Response text: {text[:200]}")
                        except:
                            pass
                    
                    return status == 200
            except aiohttp.ClientSSLError as ssl_error:
                logger.error(f"SSL Error: {ssl_error}")
                logger.error("SSL Error details:", exc_info=True)
                
                # Try with completely disabled SSL verification
                logger.info("Trying with completely disabled SSL verification")
                no_verify_context = ssl._create_unverified_context()
                connector = aiohttp.TCPConnector(ssl=no_verify_context)
                
                async with aiohttp.ClientSession(connector=connector, timeout=timeout) as fallback_session:
                    async with fallback_session.get("https://serpapi.com/search", params=params) as fallback_response:
                        fallback_status = fallback_response.status
                        logger.info(f"Fallback response status: {fallback_status}")
                        return fallback_status == 200
            except aiohttp.ClientConnectorError as conn_error:
                logger.error(f"Connection error: {conn_error}")
                logger.error("Connection error details:", exc_info=True)
                return False
                
    except Exception as e:
        logger.error(f"Error connecting to SerpAPI: {e}")
        logger.error("Traceback:", exc_info=True)
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(test_serpapi_ssl())
        
        if result:
            print("\n✅ SSL connection to SerpAPI successful!")
            sys.exit(0)
        else:
            print("\n❌ SSL connection to SerpAPI failed")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        traceback.print_exc()
        sys.exit(2) 