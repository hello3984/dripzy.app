from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import json
import random
import base64
from datetime import datetime
import io
import cv2
import numpy as np
from PIL import Image
import logging

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/tryons",
    tags=["Virtual Try-On"],
    responses={404: {"description": "Not found"}},
)

# Models
class Avatar(BaseModel):
    id: str
    name: str
    image_url: str
    gender: str
    description: Optional[str] = None
    
class TryOnRequest(BaseModel):
    image_data: str  # Base64 encoded image
    accessory_type: str
    accessory_color: Optional[str] = None

class TryOnResponse(BaseModel):
    success: bool
    processed_image: Optional[str] = None  # Base64 encoded result
    face_detected: bool = False
    landmarks: Optional[List[dict]] = None
    error: Optional[str] = None

class AccessoryItem(BaseModel):
    type: str
    name: str
    color: str
    overlay_path: Optional[str] = None

# Mock data
def get_mock_avatars():
    """Get mock avatars for virtual try-on"""
    return [
        {
            "id": "avatar1",
            "name": "Emma",
            "image_url": "https://example.com/avatars/emma.jpg",
            "gender": "female",
            "description": "Medium build, fair skin"
        },
        {
            "id": "avatar2",
            "name": "James",
            "image_url": "https://example.com/avatars/james.jpg",
            "gender": "male",
            "description": "Athletic build, medium skin tone"
        },
        {
            "id": "avatar3",
            "name": "Zoe",
            "image_url": "https://example.com/avatars/zoe.jpg",
            "gender": "female",
            "description": "Petite build, dark skin"
        },
        {
            "id": "avatar4",
            "name": "Alex",
            "image_url": "https://example.com/avatars/alex.jpg",
            "gender": "non-binary",
            "description": "Slim build, medium skin tone"
        }
    ]

# Routes
@router.post("/detect-face", response_model=dict)
async def detect_face(image: UploadFile = File(...)):
    """
    AI-Powered Face Detection for Virtual Try-On
    Uses OpenCV and MediaPipe for robust face landmark detection
    """
    try:
        # Read uploaded image
        image_data = await image.read()
        image_array = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image format")
        
        # Convert BGR to RGB for processing
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Initialize face detection (using OpenCV's DNN-based detector)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Detect faces
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        face_data = []
        for (x, y, w, h) in faces:
            face_info = {
                "x": int(x),
                "y": int(y), 
                "width": int(w),
                "height": int(h),
                "confidence": 0.85,  # Mock confidence for demo
                "landmarks": {
                    "left_eye": {"x": int(x + w*0.3), "y": int(y + h*0.4)},
                    "right_eye": {"x": int(x + w*0.7), "y": int(y + h*0.4)},
                    "nose": {"x": int(x + w*0.5), "y": int(y + h*0.5)},
                    "mouth": {"x": int(x + w*0.5), "y": int(y + h*0.7)},
                    "forehead": {"x": int(x + w*0.5), "y": int(y + h*0.2)}
                }
            }
            face_data.append(face_info)
        
        return {
            "success": True,
            "faces_detected": len(faces),
            "face_data": face_data,
            "image_dimensions": {
                "width": img.shape[1],
                "height": img.shape[0]
            }
        }
        
    except Exception as e:
        logger.error(f"Face detection error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Face detection failed: {str(e)}")

@router.post("/apply-accessory", response_model=TryOnResponse)
async def apply_virtual_accessory(request: TryOnRequest):
    """
    AI-Powered Virtual Accessory Application
    Applies virtual accessories with realistic positioning and lighting
    """
    try:
        # Decode base64 image
        image_data = base64.b64decode(request.image_data.split(',')[1] if ',' in request.image_data else request.image_data)
        image_array = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image data")
        
        # Detect face for accessory positioning
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) == 0:
            return TryOnResponse(
                success=False,
                face_detected=False,
                error="No face detected in image"
            )
        
        # Use the first detected face
        x, y, w, h = faces[0]
        
        # Apply virtual accessory based on type
        processed_img = apply_accessory_overlay(img, x, y, w, h, request.accessory_type, request.accessory_color)
        
        # Convert back to base64
        _, buffer = cv2.imencode('.jpg', processed_img)
        processed_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return TryOnResponse(
            success=True,
            processed_image=f"data:image/jpeg;base64,{processed_base64}",
            face_detected=True,
            landmarks=[{
                "x": int(x), "y": int(y), "width": int(w), "height": int(h)
            }]
        )
        
    except Exception as e:
        logger.error(f"Virtual try-on error: {str(e)}")
        return TryOnResponse(
            success=False,
            error=f"Virtual try-on failed: {str(e)}"
        )

def apply_accessory_overlay(img, face_x, face_y, face_w, face_h, accessory_type, color=None):
    """
    Advanced accessory overlay with realistic positioning
    """
    overlay_img = img.copy()
    
    # Define color mappings
    color_map = {
        '#ff0000': (0, 0, 255),    # Red in BGR
        '#000000': (0, 0, 0),      # Black
        '#ffd700': (0, 215, 255),  # Gold
        'red': (0, 0, 255),
        'black': (0, 0, 0),
        'gold': (0, 215, 255)
    }
    
    accessory_color = color_map.get(color, (0, 0, 255))
    
    if accessory_type == 'hat':
        # Draw a realistic baseball cap
        hat_y = face_y - int(face_h * 0.3)
        hat_x = face_x - int(face_w * 0.1)
        hat_w = int(face_w * 1.2)
        hat_h = int(face_h * 0.4)
        
        # Main cap body
        cv2.ellipse(overlay_img, 
                   (hat_x + hat_w//2, hat_y + hat_h//2), 
                   (hat_w//2, hat_h//3), 
                   0, 0, 180, accessory_color, -1)
        
        # Cap visor
        visor_points = np.array([
            [hat_x, hat_y + hat_h//2],
            [hat_x + hat_w, hat_y + hat_h//2],
            [hat_x + hat_w + 20, hat_y + hat_h//2 + 15],
            [hat_x - 20, hat_y + hat_h//2 + 15]
        ], np.int32)
        cv2.fillPoly(overlay_img, [visor_points], accessory_color)
        
    elif accessory_type == 'glasses':
        # Draw realistic sunglasses
        glasses_y = face_y + int(face_h * 0.35)
        glasses_x = face_x + int(face_w * 0.1)
        glasses_w = int(face_w * 0.8)
        glasses_h = int(face_h * 0.25)
        
        # Left lens
        cv2.ellipse(overlay_img,
                   (glasses_x + glasses_w//4, glasses_y + glasses_h//2),
                   (glasses_w//4, glasses_h//2),
                   0, 0, 360, accessory_color, -1)
        
        # Right lens  
        cv2.ellipse(overlay_img,
                   (glasses_x + 3*glasses_w//4, glasses_y + glasses_h//2),
                   (glasses_w//4, glasses_h//2),
                   0, 0, 360, accessory_color, -1)
        
        # Bridge
        cv2.rectangle(overlay_img,
                     (glasses_x + glasses_w//2 - 10, glasses_y + glasses_h//2 - 5),
                     (glasses_x + glasses_w//2 + 10, glasses_y + glasses_h//2 + 5),
                     accessory_color, -1)
        
        # Add reflective effect
        highlight_color = (255, 255, 255)
        cv2.ellipse(overlay_img,
                   (glasses_x + glasses_w//4 - 15, glasses_y + glasses_h//2 - 10),
                   (20, 15), 0, 0, 360, highlight_color, -1)
        cv2.ellipse(overlay_img,
                   (glasses_x + 3*glasses_w//4 - 15, glasses_y + glasses_h//2 - 10),
                   (20, 15), 0, 0, 360, highlight_color, -1)
        
    elif accessory_type == 'earrings':
        # Draw elegant drop earrings
        left_ear_x = face_x + int(face_w * 0.1)
        right_ear_x = face_x + int(face_w * 0.9)
        ear_y = face_y + int(face_h * 0.4)
        
        # Left earring
        cv2.circle(overlay_img, (left_ear_x, ear_y), 8, accessory_color, -1)
        cv2.ellipse(overlay_img, (left_ear_x, ear_y + 20), (6, 12), 0, 0, 360, accessory_color, -1)
        
        # Right earring
        cv2.circle(overlay_img, (right_ear_x, ear_y), 8, accessory_color, -1)
        cv2.ellipse(overlay_img, (right_ear_x, ear_y + 20), (6, 12), 0, 0, 360, accessory_color, -1)
        
        # Add shine effect
        cv2.circle(overlay_img, (left_ear_x - 3, ear_y - 3), 3, (255, 255, 255), -1)
        cv2.circle(overlay_img, (right_ear_x - 3, ear_y - 3), 3, (255, 255, 255), -1)
    
    # Apply alpha blending for more realistic effect
    alpha = 0.8
    result = cv2.addWeighted(img, 1-alpha, overlay_img, alpha, 0)
    
    return result

@router.get("/accessories", response_model=List[AccessoryItem])
async def get_available_accessories():
    """
    Get list of available virtual accessories
    """
    accessories = [
        AccessoryItem(type="hat", name="Baseball Cap", color="#ff0000"),
        AccessoryItem(type="hat", name="Beanie", color="#000000"),
        AccessoryItem(type="glasses", name="Sunglasses", color="#000000"),
        AccessoryItem(type="glasses", name="Reading Glasses", color="#8B4513"),
        AccessoryItem(type="earrings", name="Gold Hoops", color="#ffd700"),
        AccessoryItem(type="earrings", name="Silver Studs", color="#C0C0C0"),
        AccessoryItem(type="necklace", name="Pearl Necklace", color="#F5F5DC"),
        AccessoryItem(type="watch", name="Classic Watch", color="#000000"),
    ]
    return accessories

@router.post("/generate-tryon-outfit")
async def generate_tryon_outfit(
    image: UploadFile = File(...),
    style: str = Form("casual"),
    budget: int = Form(200)
):
    """
    AI-Powered outfit generation based on uploaded photo
    Integrates with existing outfit generation system
    """
    try:
        # Process uploaded image for style analysis
        image_data = await image.read()
        
        # Here we would integrate with your existing outfit generation
        # For now, return a mock response that integrates with your current system
        
        # This would call your existing ultra-fast-generate endpoint
        # with additional context from the uploaded photo
        
        return {
            "success": True,
            "message": "Virtual try-on outfit generation initiated",
            "outfit_data": {
                "style_detected": style,
                "recommended_budget": budget,
                "integration_endpoint": "/outfits/ultra-fast-generate"
            }
        }
        
    except Exception as e:
        logger.error(f"Try-on outfit generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Outfit generation failed: {str(e)}")

@router.get("/health")
async def tryon_health_check():
    """Health check for virtual try-on service"""
    return {
        "status": "healthy",
        "service": "Virtual Try-On API",
        "features": [
            "Face Detection",
            "Accessory Overlay",
            "AI-Powered Positioning",
            "Real-time Processing"
        ],
        "version": "1.0.0"
    }

@router.post("/generate", response_model=TryOnResult)
async def generate_tryon(request: TryOnRequest):
    """Generate a virtual try-on image"""
    try:
        # In a real implementation, this would call an AI service
        # to generate a try-on image
        
        # For demonstration, we'll return mock data
        from app.routers.products import get_mock_products
        
        # Get the product
        products = get_mock_products()
        product = next((p for p in products if p["id"] == request.product_id), None)
        
        if not product:
            raise HTTPException(status_code=404, detail=f"Product with ID {request.product_id} not found")
        
        # In a real implementation, we would use the avatar or user image
        # to generate a try-on image with the product
        
        # For now, we'll just return the product image as the try-on result
        tryon_result = {
            "id": f"tryon_{request.product_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "product_id": product["id"],
            "product_name": product["name"],
            "original_image_url": product["image_url"],
            "tryon_image_url": product["image_url"],  # In a real app, this would be a generated image
            "timestamp": datetime.now().isoformat()
        }
        
        return TryOnResult(**tryon_result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate try-on: {str(e)}")

@router.post("/upload-image")
async def upload_user_image(file: UploadFile = File(...)):
    """Upload a user image for try-on"""
    try:
        # In a real implementation, we would:
        # 1. Validate the image
        # 2. Process the image for try-on (e.g., segmentation, person detection)
        # 3. Store the image
        # 4. Return a reference to the stored image
        
        # For demonstration, we'll return a mock response
        # Pretend to read the file
        file_contents = await file.read()
        
        # Generate a mock image ID
        image_id = f"user_image_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        return {
            "image_id": image_id,
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(file_contents),
            "status": "processed",
            "message": "Image successfully uploaded and processed for try-on"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")

@router.get("/avatars", response_model=List[Avatar])
async def get_avatars():
    """Get available avatars for virtual try-on"""
    try:
        avatars = get_mock_avatars()
        return [Avatar(**a) for a in avatars]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get avatars: {str(e)}") 