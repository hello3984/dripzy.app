from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv
from typing import List, Optional

# Load environment variables
load_dotenv()

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
    
    # External API keys
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    SERPAPI_API_KEY: Optional[str] = os.getenv("SERPAPI_API_KEY")
    
    # Caching
    CACHE_TTL_SHORT: int = 300  # 5 minutes
    CACHE_TTL_MEDIUM: int = 3600  # 1 hour
    CACHE_TTL_LONG: int = 86400  # 24 hours
    
    # Update for Pydantic v2 compatibility
    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "allow"  # Allow extra fields
    }

# Create settings object
settings = Settings() 