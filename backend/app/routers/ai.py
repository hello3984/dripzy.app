"""
AI router for handling AI-related requests.
"""

import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.models.outfit_models import OutfitGenerateRequest, OutfitGenerateResponse
from app.modules.outfit.services import outfit_service

# Configure logger
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ai",
    tags=["ai"],
    responses={404: {"description": "Not found"}},
)

@router.post("/generate-outfit", response_model=OutfitGenerateResponse)
async def generate_outfit(request: OutfitGenerateRequest):
    """
    Generate an outfit based on user preferences.
    
    Args:
        request: The outfit generation request.
        
    Returns:
        OutfitGenerateResponse: The generated outfit with details.
    """
    try:
        logger.info(f"Generating outfit for prompt: '{request.prompt}'")
        response = await outfit_service.generate_outfit(request)
        return response
    except Exception as e:
        logger.error(f"Error generating outfit: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate outfit: {str(e)}")

@router.get("/health")
async def health_check():
    """
    Health check endpoint for the AI services.
    
    Returns:
        JSONResponse: Health status of AI services.
    """
    try:
        # Check if Anthropic API key is configured
        if not outfit_service.anthropic_api_key:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "warning",
                    "message": "AI Fashion Assistant API is online but Anthropic API key is not configured"
                }
            )
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "online",
                "message": "AI Fashion Assistant API is functioning correctly"
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"AI Fashion Assistant API encountered an error: {str(e)}"
            }
        )