"""
Data models for the outfit module.
Contains Pydantic models for outfit generation requests and responses.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class OutfitItem(BaseModel):
    """
    A single item in an outfit, like a shirt, pants, or shoes.
    """
    product_id: str
    product_name: str
    brand: str
    category: str
    price: float
    url: Optional[str] = None
    image_url: str
    description: Optional[str] = None
    concept_description: Optional[str] = None  # The original AI-generated description
    color: Optional[str] = None
    alternatives: Optional[List[Dict[str, Any]]] = []  # List of alternative products
    is_fallback: Optional[bool] = False  # Flag to indicate if this is a fallback item


class Outfit(BaseModel):
    """
    A complete outfit consisting of multiple items.
    """
    id: str
    name: str
    description: str
    style: str
    occasion: Optional[str] = "casual"
    items: List[OutfitItem]
    total_price: float = 0.0
    image_url: Optional[str] = None
    collage_url: Optional[str] = None
    brand_display: Optional[Dict[str, str]] = {}
    stylist_rationale: Optional[str] = None


class OutfitGenerateRequest(BaseModel):
    """
    Request model for generating outfits.
    """
    prompt: str
    gender: Optional[str] = "unisex"
    budget: Optional[float] = None
    preferred_brands: Optional[List[str]] = []
    preferred_colors: Optional[List[str]] = []
    excluded_categories: Optional[List[str]] = []
    include_alternatives: Optional[bool] = True  # Flag to include alternatives


class OutfitGenerateResponse(BaseModel):
    """
    Response model for generated outfits.
    """
    outfits: List[Outfit]
    prompt: str 