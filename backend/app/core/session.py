import uuid
from typing import Dict, Any, Optional, List
import time
import logging
import json
from app.core.cache import cache_service

# Configure logger
logger = logging.getLogger(__name__)

class SessionManager:
    """
    Session manager for maintaining persistent user sessions and outfit search history.
    Uses UUID to create shareable, persistent sessions.
    """
    
    def __init__(self):
        # Sessions are stored in the long-term cache
        self.cache_level = "long"
    
    def create_session(self, session_type: str = "outfit") -> Dict[str, Any]:
        """
        Create a new session with UUID
        
        Args:
            session_type: Type of session (outfit, search, etc.)
            
        Returns:
            Session object with ID
        """
        session_id = str(uuid.uuid4())
        
        session = {
            "id": session_id,
            "type": session_type,
            "created_at": time.time(),
            "data": {},
            "history": []
        }
        
        # Store in cache
        cache_key = f"session_{session_id}"
        cache_service.set(cache_key, session, self.cache_level)
        
        logger.info(f"Created new {session_type} session: {session_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a session by ID
        
        Args:
            session_id: Session UUID
            
        Returns:
            Session object or None if not found
        """
        cache_key = f"session_{session_id}"
        session = cache_service.get(cache_key, self.cache_level)
        
        if session:
            logger.debug(f"Retrieved session: {session_id}")
        else:
            logger.debug(f"Session not found: {session_id}")
            
        return session
    
    def update_session(self, session_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update session data
        
        Args:
            session_id: Session UUID
            data: Data to update
            
        Returns:
            Updated session or None if not found
        """
        session = self.get_session(session_id)
        
        if not session:
            logger.warning(f"Cannot update non-existent session: {session_id}")
            return None
        
        # Update data
        session["data"].update(data)
        session["updated_at"] = time.time()
        
        # Add to history if significant change
        if "prompt" in data or "outfit" in data:
            # Remove sensitive or large data
            history_entry = {
                "timestamp": time.time(),
                "action": "update",
            }
            
            if "prompt" in data:
                history_entry["prompt"] = data["prompt"]
            
            if "outfit" in data and "id" in data["outfit"]:
                history_entry["outfit_id"] = data["outfit"]["id"]
            
            session["history"].append(history_entry)
        
        # Store updated session
        cache_key = f"session_{session_id}"
        cache_service.set(cache_key, session, self.cache_level)
        
        logger.debug(f"Updated session: {session_id}")
        return session
    
    def add_outfit_to_session(self, session_id: str, outfit: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Add an outfit to a session
        
        Args:
            session_id: Session UUID
            outfit: Outfit data
            
        Returns:
            Updated session or None if not found
        """
        session = self.get_session(session_id)
        
        if not session:
            logger.warning(f"Cannot add outfit to non-existent session: {session_id}")
            return None
        
        # Ensure outfits list exists
        if "outfits" not in session["data"]:
            session["data"]["outfits"] = []
        
        # Add outfit
        session["data"]["outfits"].append(outfit)
        session["updated_at"] = time.time()
        
        # Add to history
        history_entry = {
            "timestamp": time.time(),
            "action": "add_outfit",
            "outfit_id": outfit.get("id", "unknown")
        }
        
        session["history"].append(history_entry)
        
        # Store updated session
        cache_key = f"session_{session_id}"
        cache_service.set(cache_key, session, self.cache_level)
        
        logger.info(f"Added outfit to session: {session_id}")
        return session
    
    def get_shareable_url(self, session_id: str, base_url: str = "https://dripzy.app") -> str:
        """
        Generate shareable URL for a session
        
        Args:
            session_id: Session UUID
            base_url: Base URL for the application
            
        Returns:
            Shareable URL
        """
        session = self.get_session(session_id)
        
        if not session:
            logger.warning(f"Cannot generate URL for non-existent session: {session_id}")
            return f"{base_url}/not-found"
        
        session_type = session.get("type", "outfit")
        
        if session_type == "outfit":
            return f"{base_url}/outfit/{session_id}"
        elif session_type == "search":
            return f"{base_url}/search/{session_id}"
        else:
            return f"{base_url}/session/{session_id}"

# Create global session manager
session_manager = SessionManager() 