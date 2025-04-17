"""
Outfit module for generating fashion outfit recommendations.
"""

from app.modules.outfit.models import OutfitItem, Outfit, OutfitGenerateRequest, OutfitGenerateResponse
from app.modules.outfit.services import OutfitService

# Create service instance
outfit_service = OutfitService()

__all__ = ['OutfitItem', 'Outfit', 'OutfitGenerateRequest', 'OutfitGenerateResponse', 'outfit_service'] 