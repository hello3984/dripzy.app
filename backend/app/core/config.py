from pydantic_settings import BaseSettings
import os
import logging
from typing import List, Optional
from dotenv import load_dotenv

# Configure logger
logger = logging.getLogger(__name__)

# Load environment variables from .env file
logger.info("Attempting to load .env file...")
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
found = os.path.exists(env_path)
if found:
    load_dotenv(env_path)
    loaded = True
    logger.info(f".env file found at {env_path} and loaded")
else:
    loaded = False
    logger.info(".env file not found in expected location")

# Log status
logger.info(f".env file found and loaded: {loaded}")

class Settings(BaseSettings):
    """Application settings"""
    
    # API Information
    API_TITLE: str = "AI Fashion Assistant API"
    API_DESCRIPTION: str = "Backend API for AI Fashion Assistant with Virtual Try-On"
    API_VERSION: str = "0.1.0"
    
    # Server settings
    PORT: int = int(os.getenv("PORT", 8000))
    HOST: str = "0.0.0.0"
    RELOAD: bool = True
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]  # Allow all origins for development
    
    # External API keys - Pydantic will load these from .env via model_config
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # To get a SerpAPI key:
    # 1. Sign up at https://serpapi.com/
    # 2. Get your API key from your dashboard
    # 3. Add SERPAPI_API_KEY=your_key_here to the .env file
    SERPAPI_API_KEY: Optional[str] = None
    
    # Caching
    CACHE_TTL_SHORT: int = 300  # 5 minutes
    CACHE_TTL_MEDIUM: int = 3600  # 1 hour
    CACHE_TTL_LONG: int = 86400  # 24 hours
    
    # Update for Pydantic v2 compatibility
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }

    def __init__(self, **data):
        logger.info("Creating settings instance...")
        # Log key availability without exposing values
        if "ANTHROPIC_API_KEY" in os.environ or "ANTHROPIC_API_KEY" in data:
            logger.info("ANTHROPIC_API_KEY loaded: Exists")
        else:
            logger.info("ANTHROPIC_API_KEY loaded: Not Found")
            
        if "SERPAPI_API_KEY" in os.environ or "SERPAPI_API_KEY" in data:
            logger.info("SERPAPI_API_KEY loaded: Exists")
        else:
            logger.info("SERPAPI_API_KEY loaded: Not Found")
        
        super().__init__(**data)
        logger.info("Settings instance created.")

# Create settings object
settings = Settings() 