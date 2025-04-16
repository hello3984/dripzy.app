"""
Data models for the outfit module.
Contains Pydantic models for outfit generation requests and responses.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class OutfitItem(BaseModel):
    """Model representing a single item in an outfit."""
    product_id: Optional[str] = Field(None, description="Product identifier")
    name: str = Field(..., description="Name of the item")
    product_name: Optional[str] = Field(None, description="Product name (for compatibility)")
    category: str = Field(..., description="Category of the item (Top, Bottom, Shoes, etc.)")
    description: Optional[str] = Field(None, description="Description of the item")
    color: Optional[str] = Field(None, description="Primary color of the item")
    price: float = Field(..., description="Price of the item")
    brand: Optional[str] = Field(None, description="Brand of the item")
    image_url: Optional[str] = Field(None, description="URL to the image of the item")
    url: Optional[str] = Field(None, description="URL to purchase the item")


class Outfit(BaseModel):
    """Model representing a complete outfit with multiple items."""
    id: str = Field(..., description="Unique identifier for the outfit")
    name: str = Field(..., description="Name of the outfit")
    description: str = Field(..., description="Description of the outfit")
    style: Optional[str] = Field("Contemporary", description="Style of the outfit")
    occasion: Optional[str] = Field("Casual", description="Occasion the outfit is suitable for")
    items: List[OutfitItem] = Field(..., description="List of items in the outfit")
    total_price: float = Field(..., description="Total price of all items in the outfit")
    style_tags: Optional[List[str]] = Field(default_factory=list, description="Style tags associated with the outfit")
    collage_image: Optional[str] = Field(None, description="Base64 encoded collage image of the outfit")
    image_map: Optional[Dict[str, Any]] = Field(None, description="Coordinates for clickable areas in the collage")
    brand_display: Optional[Dict[str, str]] = Field(None, description="Brands displayed by category")


class OutfitGenerateRequest(BaseModel):
    """Model for outfit generation request parameters."""
    prompt: str = Field(..., description="User's outfit request prompt")
    gender: Optional[str] = Field("unisex", description="Gender preference (male, female, unisex)")
    budget: Optional[float] = Field(None, description="Maximum budget for the outfit")
    preferred_brands: Optional[List[str]] = Field(None, description="Preferred brands")
    preferred_categories: Optional[List[str]] = Field(None, description="Preferred categories")
    style_keywords: Optional[List[str]] = Field(None, description="Style keywords")
    include: Optional[str] = Field(None, description="Items to include in the outfit")


class OutfitGenerateResponse(BaseModel):
    """Model for outfit generation response."""
    outfits: List[Outfit] = Field(..., description="Generated outfits")
    prompt: str = Field(..., description="Original prompt that was processed")
    collage_image: Optional[str] = Field(None, description="Base64 encoded image of the outfit collage")
    image_map: Optional[Dict[str, Any]] = Field(None, description="Clickable areas for the collage")
    status: Optional[str] = Field("success", description="Status of the response (success, limited)")
    status_message: Optional[str] = Field(None, description="Message explaining the status")
    using_fallbacks: Optional[bool] = Field(False, description="Whether fallback products are being used") 