import time
import json
import logging
from typing import Dict, Any, Optional, Union, List
from difflib import SequenceMatcher

# Configure logger
logger = logging.getLogger(__name__)

class CacheService:
    """
    Service for caching data with different TTL levels
    """
    
    def __init__(self):
        # Initialize cache storage for different time-to-live levels
        self._cache = {
            "short": {},  # 5 minutes
            "medium": {}, # 1 hour
            "long": {}    # 24 hours
        }
        
        # Define TTL values in seconds
        self._ttl = {
            "short": 300,      # 5 minutes
            "medium": 3600,    # 1 hour
            "long": 86400      # 24 hours
        }
        
        logger.info("Cache service initialized")
    
    def get(self, key: str, level: str = "medium") -> Optional[Any]:
        """
        Get value from cache if it exists and is not expired
        
        Args:
            key: Cache key
            level: Cache level (short, medium, long)
            
        Returns:
            Cached value or None if not found or expired
        """
        if level not in self._cache:
            logger.warning(f"Invalid cache level: {level}")
            level = "medium"
            
        if key in self._cache[level]:
            entry = self._cache[level][key]
            
            # Check if entry is expired
            if time.time() < entry["expires"]:
                logger.debug(f"Cache hit: {key} (level: {level})")
                return entry["data"]
            else:
                # Remove expired entry
                logger.debug(f"Cache expired: {key} (level: {level})")
                del self._cache[level][key]
                
        return None
    
    def set(self, key: str, value: Any, level: str = "medium") -> None:
        """
        Set value in cache with the specified TTL level
        
        Args:
            key: Cache key
            value: Value to cache
            level: Cache level (short, medium, long)
        """
        if level not in self._cache:
            logger.warning(f"Invalid cache level: {level}")
            level = "medium"
        
        # Calculate expiration time
        expires = time.time() + self._ttl[level]
        
        # Store value with expiration time
        self._cache[level][key] = {
            "data": value,
            "expires": expires
        }
        
        logger.debug(f"Cache set: {key} (level: {level})")
    
    def delete(self, key: str, level: str = None) -> None:
        """
        Delete value from cache
        
        Args:
            key: Cache key
            level: Cache level (short, medium, long) or None to delete from all levels
        """
        if level is None:
            # Delete from all levels
            for l in self._cache:
                if key in self._cache[l]:
                    del self._cache[l][key]
                    logger.debug(f"Cache deleted: {key} (level: {l})")
        elif level in self._cache:
            # Delete from specific level
            if key in self._cache[level]:
                del self._cache[level][key]
                logger.debug(f"Cache deleted: {key} (level: {level})")
        else:
            logger.warning(f"Invalid cache level: {level}")
    
    def clear(self, level: str = None) -> None:
        """
        Clear all cached values
        
        Args:
            level: Cache level (short, medium, long) or None to clear all levels
        """
        if level is None:
            # Clear all levels
            for l in self._cache:
                self._cache[l] = {}
                logger.info(f"Cache cleared: level {l}")
        elif level in self._cache:
            # Clear specific level
            self._cache[level] = {}
            logger.info(f"Cache cleared: level {level}")
        else:
            logger.warning(f"Invalid cache level: {level}")
    
    def clean_expired(self) -> None:
        """
        Remove all expired entries from cache
        """
        current_time = time.time()
        
        for level in self._cache:
            keys_to_delete = []
            
            for key, entry in self._cache[level].items():
                if current_time > entry["expires"]:
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                del self._cache[level][key]
            
            if keys_to_delete:
                logger.debug(f"Cleaned {len(keys_to_delete)} expired entries from {level} cache")
    
    def find_similar(self, key_prefix: str, threshold: float = 0.8, level: str = "medium") -> Optional[Any]:
        """
        Find a similar key in the cache based on string similarity
        
        Args:
            key_prefix: Cache key prefix to match
            threshold: Similarity threshold (0.0 to 1.0)
            level: Cache level (short, medium, long)
            
        Returns:
            Cached value for the most similar key, or None if no similar key found
        """
        if level not in self._cache:
            logger.warning(f"Invalid cache level: {level}")
            return None
        
        best_match = None
        best_ratio = 0
        
        # Find best matching key
        for cache_key in self._cache[level]:
            if not cache_key.startswith(key_prefix.split("_")[0]):
                continue
                
            ratio = SequenceMatcher(None, key_prefix, cache_key).ratio()
            
            if ratio >= threshold and ratio > best_ratio:
                best_ratio = ratio
                best_match = cache_key
        
        if best_match:
            entry = self._cache[level][best_match]
            
            # Check if entry is expired
            if time.time() < entry["expires"]:
                logger.debug(f"Similar cache hit: {best_match} for {key_prefix} (ratio: {best_ratio:.2f})")
                return entry["data"]
        
        return None
    
    def _get_cache_by_level(self, level: str) -> Dict[str, Dict[str, Any]]:
        """
        Get the cache dictionary for a specific level
        
        Args:
            level: Cache level (short, medium, long)
            
        Returns:
            Cache dictionary for the level
        """
        if level in self._cache:
            return self._cache[level]
        return {}
    
    def get_stats(self) -> Dict[str, Dict[str, int]]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache statistics by level
        """
        stats = {}
        current_time = time.time()
        
        for level in self._cache:
            active_count = 0
            expired_count = 0
            
            for key, entry in self._cache[level].items():
                if current_time < entry["expires"]:
                    active_count += 1
                else:
                    expired_count += 1
            
            stats[level] = {
                "active": active_count,
                "expired": expired_count,
                "total": active_count + expired_count
            }
        
        return stats

# Create global cache service instance
cache_service = CacheService() 