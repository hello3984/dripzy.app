"""
Service for generating outfit collages from product images.
"""

import base64
import io
import logging
import os
from typing import List, Dict, Any, Optional, Tuple

import requests
from PIL import Image, ImageDraw

logger = logging.getLogger(__name__)

class CollageService:
    """
    Service for creating collage images from product images.
    Arranges images in a visually appealing layout with clickable areas.
    """
    
    def __init__(self):
        """Initialize the CollageService."""
        self.canvas_width = 800
        self.canvas_height = 800
        self.padding = 20
        
    def create_collage(self, image_urls: List[str], categories: List[str]) -> Dict[str, Any]:
        """
        Create a collage from a list of product image URLs.
        
        Args:
            image_urls: List of image URLs to include in the collage
            categories: List of product categories corresponding to the images
            
        Returns:
            Dict containing the collage image as base64 and image map coordinates
        """
        logger.info(f"Creating collage from {len(image_urls)} images")
        
        if not image_urls:
            logger.warning("No images provided for collage creation")
            return {"image": None, "map": {}}
            
        try:
            # Download images
            images = self._download_images(image_urls)
            if not images:
                logger.warning("Failed to download any images for collage")
                return {"image": None, "map": {}}
                
            # Create layout based on number and type of products
            layout = self._create_layout(categories, len(images))
            
            # Create the collage image
            collage, image_map = self._generate_collage(images, categories, layout)
            
            # Convert to base64
            buffered = io.BytesIO()
            collage.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            return {
                "image": img_str,
                "map": image_map
            }
        except Exception as e:
            logger.error(f"Error creating collage: {e}")
            return {"image": None, "map": {}}
    
    # Alias for compatibility with existing code
    def create_outfit_collage(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a collage from a list of item dictionaries.
        
        Args:
            items: List of item dictionaries with image_url and category
            
        Returns:
            Dict containing the collage image as base64 and image map coordinates
        """
        image_urls = [item.get("image_url") for item in items if item.get("image_url")]
        categories = [item.get("category") for item in items if item.get("image_url")]
        
        result = self.create_collage(image_urls, categories)
        
        # Format response for compatibility
        return {
            "image": result.get("image"),
            "map": result.get("map"),
            # For backwards compatibility
            "collage_base64": result.get("image"),
            "image_map": result.get("map")
        }
            
    def _download_images(self, image_urls: List[str]) -> List[Optional[Image.Image]]:
        """
        Download images from URLs.
        
        Args:
            image_urls: List of image URLs
            
        Returns:
            List of PIL Image objects
        """
        images = []
        
        for url in image_urls:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    img = Image.open(io.BytesIO(response.content))
                    # Convert to RGB if necessary (e.g., for PNGs with transparency)
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    images.append(img)
                else:
                    logger.warning(f"Failed to download image from {url}, status code: {response.status_code}")
                    images.append(None)
            except Exception as e:
                logger.error(f"Error downloading image from {url}: {e}")
                images.append(None)
                
        return [img for img in images if img is not None]
        
    def _create_layout(self, categories: List[str], num_images: int) -> Dict[str, Tuple[int, int, int, int]]:
        """
        Create a layout for the collage based on the categories.
        
        Args:
            categories: List of product categories
            num_images: Number of images to layout
            
        Returns:
            Dictionary mapping indices to [x, y, width, height] rectangles
        """
        layout = {}
        
        # Determine layout based on number of images
        if num_images == 1:
            # Single image gets full canvas
            layout[0] = (0, 0, self.canvas_width, self.canvas_height)
        elif num_images == 2:
            # Two images side by side
            layout[0] = (0, 0, self.canvas_width // 2 - self.padding // 2, self.canvas_height)
            layout[1] = (self.canvas_width // 2 + self.padding // 2, 0, 
                        self.canvas_width // 2 - self.padding // 2, self.canvas_height)
        elif num_images == 3:
            # Top image takes full width, bottom two side by side
            layout[0] = (0, 0, self.canvas_width, self.canvas_height // 2 - self.padding // 2)
            layout[1] = (0, self.canvas_height // 2 + self.padding // 2, 
                        self.canvas_width // 2 - self.padding // 2, 
                        self.canvas_height // 2 - self.padding // 2)
            layout[2] = (self.canvas_width // 2 + self.padding // 2, 
                        self.canvas_height // 2 + self.padding // 2,
                        self.canvas_width // 2 - self.padding // 2, 
                        self.canvas_height // 2 - self.padding // 2)
        else:
            # Grid layout for 4+ images
            cols = 2
            rows = (num_images + 1) // 2
            cell_width = (self.canvas_width - (cols - 1) * self.padding) // cols
            cell_height = (self.canvas_height - (rows - 1) * self.padding) // rows
            
            for i in range(num_images):
                col = i % cols
                row = i // cols
                x = col * (cell_width + self.padding)
                y = row * (cell_height + self.padding)
                layout[i] = (x, y, cell_width, cell_height)
                
        return layout
        
    def _generate_collage(self, images: List[Image.Image], categories: List[str], 
                        layout: Dict[int, Tuple[int, int, int, int]]) -> Tuple[Image.Image, Dict[str, List[int]]]:
        """
        Generate the collage image and image map.
        
        Args:
            images: List of downloaded images
            categories: List of product categories
            layout: Layout dictionary mapping indices to rectangles
            
        Returns:
            Tuple of (PIL Image, image map dictionary)
        """
        # Create blank canvas
        collage = Image.new('RGB', (self.canvas_width, self.canvas_height), color='white')
        image_map = {}
        
        # Place each image according to layout
        for i, (img, category) in enumerate(zip(images, categories[:len(images)])):
            if i not in layout:
                continue
                
            x, y, width, height = layout[i]
            
            # Resize image to fit in the allocated space
            img_resized = self._resize_image(img, width, height)
            
            # Center image in its space
            paste_x = x + (width - img_resized.width) // 2
            paste_y = y + (height - img_resized.height) // 2
            
            # Paste image onto canvas
            collage.paste(img_resized, (paste_x, paste_y))
            
            # Add to image map
            image_map[category] = [paste_x, paste_y, paste_x + img_resized.width, paste_y + img_resized.height]
            
        return collage, image_map
        
    def _resize_image(self, img: Image.Image, target_width: int, target_height: int) -> Image.Image:
        """
        Resize image while maintaining aspect ratio.
        
        Args:
            img: PIL Image to resize
            target_width: Target width
            target_height: Target height
            
        Returns:
            Resized PIL Image
        """
        width, height = img.size
        aspect = width / height
        
        if width > height:
            # Landscape orientation
            new_width = target_width
            new_height = int(new_width / aspect)
            
            if new_height > target_height:
                new_height = target_height
                new_width = int(new_height * aspect)
        else:
            # Portrait orientation
            new_height = target_height
            new_width = int(new_height * aspect)
            
            if new_width > target_width:
                new_width = target_width
                new_height = int(new_width / aspect)
                
        return img.resize((new_width, new_height), Image.LANCZOS)

# Create a singleton instance of the CollageService
collage_service = CollageService() 