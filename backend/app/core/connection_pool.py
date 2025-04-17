"""
Connection Pool Manager
----------------------
Manages HTTP client connection pools for the application.
Ensures efficient resource usage and proper cleanup.
"""

import logging
import httpx
import ssl
import asyncio
from typing import Optional, Dict, Any

# Configure logging
logger = logging.getLogger(__name__)

class ConnectionPoolManager:
    """
    Manages connection pools for external API services.
    Provides optimized clients with connection pooling and timeout settings.
    """
    
    def __init__(self):
        """Initialize connection pools"""
        self._clients: Dict[str, httpx.AsyncClient] = {}
        self._limits = httpx.Limits(
            max_connections=20,
            max_keepalive_connections=10,
            keepalive_expiry=30.0  # 30 seconds
        )
        
        # Default timeout configuration (10s connect, 30s read)
        self._timeout = httpx.Timeout(30.0, connect=10.0)
        
        # Create custom SSL context
        try:
            self._ssl_context = ssl.create_default_context()
            logger.info("Created default SSL context for connection pools")
        except Exception as e:
            logger.warning(f"Could not create default SSL context: {e}")
            self._ssl_context = ssl._create_unverified_context()
            logger.warning("Using unverified SSL context due to error")
    
    async def get_client(self, name: str, **kwargs) -> httpx.AsyncClient:
        """
        Get or create a client for a specific service.
        
        Args:
            name: Unique name for the client
            **kwargs: Override default client settings
            
        Returns:
            AsyncClient: HTTP client with connection pooling
        """
        if name not in self._clients or self._clients[name].is_closed:
            # Create a new client if doesn't exist or is closed
            limits = kwargs.pop('limits', self._limits)
            timeout = kwargs.pop('timeout', self._timeout)
            verify = kwargs.pop('verify', self._ssl_context)
            
            self._clients[name] = httpx.AsyncClient(
                limits=limits,
                timeout=timeout,
                verify=verify,
                **kwargs
            )
            logger.info(f"Created new connection pool for {name}")
            
        return self._clients[name]
    
    async def close_all(self):
        """Close all connection pools gracefully"""
        close_tasks = []
        for name, client in self._clients.items():
            if not client.is_closed:
                logger.info(f"Closing connection pool {name}")
                close_tasks.append(client.aclose())
        
        if close_tasks:
            await asyncio.gather(*close_tasks)
            logger.info("Successfully closed all connection pools")
    
    async def close(self, name: str):
        """Close a specific connection pool"""
        if name in self._clients and not self._clients[name].is_closed:
            await self._clients[name].aclose()
            logger.info(f"Closed connection pool {name}")

# Create a global singleton instance
pool_manager = ConnectionPoolManager()

# Function to get the singleton instance
def get_connection_pool():
    """Get the global connection pool manager"""
    return pool_manager 