import os
import io
import requests
import base64
import logging
import random
import re
from PIL import Image, ImageDraw, ImageFont
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus
from io import BytesIO

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get Google API credentials
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

def get_images_from_web(query, num_images=4, category=None):
    """
    Get images from multiple sources based on a search query
    """
    # Improve the search query with more targeted terms based on category
    enhanced_query = query
    if category:
        category_terms = {
            "Top": "clothing fashion top blouse shirt",
            "Bottom": "clothing fashion pants jeans shorts skirt",
            "Dress": "clothing fashion dress",
            "Outerwear": "clothing fashion jacket coat cardigan outerwear",
            "Shoes": "fashion shoes boots sandals footwear",
            "Accessories": "fashion accessories jewelry bag purse",
        }
        if category in category_terms:
            enhanced_query = f"{query} {category_terms[category]}"
    
    # Try to get images from Bing first
    try:
        bing_results = get_bing_images(enhanced_query, num_images)
        if bing_results and len(bing_results) >= num_images:
            return bing_results
    except Exception as e:
        print(f"Error fetching Bing images: {str(e)}")
    
    # Fall back to unsplash if Bing fails
    try:
        unsplash_results = get_unsplash_images(enhanced_query, num_images)
        if unsplash_results:
            return unsplash_results
    except Exception as e:
        print(f"Error fetching Unsplash images: {str(e)}")
    
    # Last resort - try Google images
    try:
        google_results = get_google_images(enhanced_query, num_images)
        if google_results:
            return google_results
    except Exception as e:
        print(f"Error fetching Google images: {str(e)}")
    
    # If all else fails, return placeholder images
    placeholder_images = []
    for i in range(num_images):
        placeholder_images.append({
            "image_url": f"https://via.placeholder.com/300x400?text={category or 'Item'}+{i+1}",
            "source_url": "#"
        })
    
    return placeholder_images

def get_bing_images(query: str, num_images: int = 5) -> List[Dict[str, str]]:
    """
    Get images from Bing image search
    """
    try:
        # Format search query
        encoded_query = quote_plus(query)
        
        # Try Bing image search
        bing_url = f"https://www.bing.com/images/search?q={encoded_query}&form=HDRSC2&first=1"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(bing_url, headers=headers, timeout=8)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Find image elements (specific to Bing's structure)
            img_tags = soup.find_all('img', {'class': 'mimg'})
            image_results = []
            for img in img_tags:
                if 'src' in img.attrs and img['src'].startswith('http'):
                    # Find parent link
                    parent_a = img.find_parent('a')
                    source_url = parent_a.get('href') if parent_a else bing_url
                    if not source_url.startswith('http'):
                        source_url = f"https://bing.com{source_url}" if source_url.startswith('/') else bing_url
                    
                    image_results.append({
                        'image_url': img['src'],
                        'source_url': source_url
                    })
                elif 'data-src' in img.attrs and img['data-src'].startswith('http'):
                    parent_a = img.find_parent('a')
                    source_url = parent_a.get('href') if parent_a else bing_url
                    if not source_url.startswith('http'):
                        source_url = f"https://bing.com{source_url}" if source_url.startswith('/') else bing_url
                        
                    image_results.append({
                        'image_url': img['data-src'],
                        'source_url': source_url
                    })
            
            # Filter out small images (likely thumbnails or icons)
            filtered_results = []
            for result in image_results:
                url = result['image_url']
                if not ('icon' in url.lower() or 'thumbnail' in url.lower() or 'logo' in url.lower()):
                    if url.endswith(('.jpg', '.jpeg', '.png', '.webp')) or 'images' in url.lower():
                        filtered_results.append(result)
            
            if not filtered_results:
                logger.warning(f"No images found for query: {query}")
                return []
            
            # Return a random subset of the results
            if len(filtered_results) > num_images:
                filtered_results = random.sample(filtered_results, num_images)
            
            return filtered_results
    
    except Exception as e:
        logger.error(f"Error searching for images: {str(e)}")
        return []

def get_unsplash_images(query: str, num_images: int = 5) -> List[Dict[str, str]]:
    """
    Get images from Unsplash
    """
    try:
        # Format search query
        encoded_query = quote_plus(query)
        
        # Try Unsplash
        unsplash_url = f"https://unsplash.com/s/photos/{encoded_query.replace('+', '-')}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(unsplash_url, headers=headers, timeout=8)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            img_tags = soup.find_all('img')
            image_results = []
            for img in img_tags:
                if 'src' in img.attrs and 'images.unsplash.com' in img['src']:
                    # Find parent link or figure
                    parent = img.find_parent('a') or img.find_parent('figure')
                    source_url = unsplash_url
                    if parent and parent.name == 'a' and parent.get('href'):
                        source_url = parent['href']
                        if not source_url.startswith('http'):
                            source_url = f"https://unsplash.com{source_url}" if source_url.startswith('/') else unsplash_url
                            
                    image_results.append({
                        'image_url': img['src'],
                        'source_url': source_url
                    })
            
            # Filter out small images (likely thumbnails or icons)
            filtered_results = []
            for result in image_results:
                url = result['image_url']
                if not ('icon' in url.lower() or 'thumbnail' in url.lower() or 'logo' in url.lower()):
                    if url.endswith(('.jpg', '.jpeg', '.png', '.webp')) or 'images' in url.lower():
                        filtered_results.append(result)
            
            if not filtered_results:
                logger.warning(f"No images found for query: {query}")
                return []
            
            # Return a random subset of the results
            if len(filtered_results) > num_images:
                filtered_results = random.sample(filtered_results, num_images)
            
            return filtered_results
    
    except Exception as e:
        logger.error(f"Error searching for images: {str(e)}")
        return []

def get_google_images(query: str, num_images: int = 5, category: str = None) -> List[str]:
    """
    Compatibility function that returns just the image URLs
    """
    results = get_images_from_web(query, num_images, category)
    # Return just the image URLs for backward compatibility
    return [result['image_url'] for result in results]

def get_mock_images(category: str = None, num_images: int = 5) -> List[Dict[str, str]]:
    """
    Return mock image URLs when web scraping is not available
    """
    # Map categories to placeholder image URLs for Coachella styles with sources
    category_images = {
        "Top": [
            {"image_url": "https://i.etsystatic.com/36130151/r/il/70c1b0/4037856960/il_fullxfull.4037856960_4yz2.jpg", 
             "source_url": "https://www.etsy.com/listing/1445005112/"},
            {"image_url": "https://i.pinimg.com/originals/c5/38/25/c538250266738758a0252c95c4b99751.jpg",
             "source_url": "https://www.pinterest.com/pin/c538250266738758a0252c95c4b99751/"},
            {"image_url": "https://di2ponv0v5otw.cloudfront.net/posts/2023/01/21/63cc3ca8a0aeb7d56bc276c2/m_63cc3cb9dff94d669a55e63d.jpg",
             "source_url": "https://poshmark.com/listing/63cc3ca8a0aeb7d56bc276c2"}
        ],
        "Bottom": [
            {"image_url": "https://i.pinimg.com/originals/d3/0b/a5/d30ba5c0a6d32d1a231b9c649bc5d1f0.jpg",
             "source_url": "https://www.pinterest.com/pin/d30ba5c0a6d32d1a231b9c649bc5d1f0/"},
            {"image_url": "https://i.pinimg.com/736x/4e/77/fa/4e77fa9ca5b3956ffb2312cea3f4a0cc.jpg",
             "source_url": "https://www.pinterest.com/pin/4e77fa9ca5b3956ffb2312cea3f4a0cc/"},
            {"image_url": "https://media.boohoo.com/i/boohoo/bzz94119_white_xl/female-white-premium-crochet-shorts/?w=900&qlt=default&fmt.jp2.qlt=70&fmt=auto&sm=fit",
             "source_url": "https://www.boohoo.com/womens/shorts/crochet-shorts"}
        ],
        "Dress": [
            {"image_url": "https://i.pinimg.com/736x/9f/95/68/9f95686aa183ec27800262fc054a2dc3.jpg",
             "source_url": "https://www.pinterest.com/pin/9f95686aa183ec27800262fc054a2dc3/"},
            {"image_url": "https://i.pinimg.com/originals/12/1d/21/121d219c4b4cbeffcf2915275e22df05.png",
             "source_url": "https://www.pinterest.com/pin/121d219c4b4cbeffcf2915275e22df05/"},
            {"image_url": "https://i.etsystatic.com/31755905/r/il/9c8f31/3766105531/il_fullxfull.3766105531_9aou.jpg",
             "source_url": "https://www.etsy.com/listing/1211002733/"}
        ],
        "Shoes": [
            {"image_url": "https://i.pinimg.com/originals/af/a5/7a/afa57a1151975127bc938e4aa830f12d.jpg",
             "source_url": "https://www.pinterest.com/pin/afa57a1151975127bc938e4aa830f12d/"},
            {"image_url": "https://i.pinimg.com/originals/8e/9c/99/8e9c9937660079252398cbad9b6ded8e.jpg",
             "source_url": "https://www.pinterest.com/pin/8e9c9937660079252398cbad9b6ded8e/"},
            {"image_url": "https://i.pinimg.com/originals/c9/a3/41/c9a341af0a0a3f328b5722e22caba21e.jpg",
             "source_url": "https://www.pinterest.com/pin/c9a341af0a0a3f328b5722e22caba21e/"}
        ],
        "Accessory": [
            {"image_url": "https://i.etsystatic.com/28745968/r/il/0f66a8/3838079152/il_fullxfull.3838079152_9n65.jpg",
             "source_url": "https://www.etsy.com/listing/1211002734/"},
            {"image_url": "https://di2ponv0v5otw.cloudfront.net/posts/2023/02/22/63f65ec517e49c7e39cf8f4c/m_63f65ee08d7a3cdeba7e3af9.jpg",
             "source_url": "https://poshmark.com/listing/63f65ec517e49c7e39cf8f4c"},
            {"image_url": "https://i.etsystatic.com/37223776/r/il/7cad57/4287082262/il_fullxfull.4287082262_sczb.jpg",
             "source_url": "https://www.etsy.com/listing/1211002735/"}
        ],
        "Outerwear": [
            {"image_url": "https://img.theimpression.com/a3bbb3f0fec7e1663ac38e4a3ba5f9cc/street-style-coachella-2023-d3-theimpression-04.jpg",
             "source_url": "https://theimpression.com/street-style-coachella-2023/"},
            {"image_url": "https://i.pinimg.com/originals/96/1a/09/961a09b58ca7517f8aa56e9fd0e42134.jpg",
             "source_url": "https://www.pinterest.com/pin/961a09b58ca7517f8aa56e9fd0e42134/"},
            {"image_url": "https://i.pinimg.com/originals/96/2b/05/962b05f557ace5392eb749dd30561f5c.jpg",
             "source_url": "https://www.pinterest.com/pin/962b05f557ace5392eb749dd30561f5c/"}
        ]
    }
    
    # Coachella-specific festival images
    coachella_images = [
        {"image_url": "https://i.pinimg.com/originals/1b/3b/5f/1b3b5f9068305b8954813db44e8d6880.jpg",
         "source_url": "https://www.pinterest.com/pin/1b3b5f9068305b8954813db44e8d6880/"},
        {"image_url": "https://i.pinimg.com/736x/95/af/d2/95afd25eb65d1b79d7f20f4f4696c7d0.jpg",
         "source_url": "https://www.pinterest.com/pin/95afd25eb65d1b79d7f20f4f4696c7d0/"},
        {"image_url": "https://fashionista.com/.image/t_share/MTk3MDQxMjI1NTI0OTQ0OTQ2/coachella-2023-street-style-day-3-2.jpg",
         "source_url": "https://fashionista.com/2023/04/coachella-2023-street-style"},
        {"image_url": "https://i.pinimg.com/originals/4d/de/a9/4ddea90c555153040687557ff3a7c4f4.jpg",
         "source_url": "https://www.pinterest.com/pin/4ddea90c555153040687557ff3a7c4f4/"},
        {"image_url": "https://img.theimpression.com/da81a47d7cd8e4ee9ee75fc9caaff39a/street-style-coachella-2023-d3-theimpression-11.jpg",
         "source_url": "https://theimpression.com/street-style-coachella-2023/"}
    ]
    
    # Get images for the specified category or use default
    if category and category in category_images:
        available_images = category_images[category]
    elif "festival" in str(category).lower() or "coachella" in str(category).lower():
        available_images = coachella_images
    else:
        available_images = coachella_images
    
    # Make sure we have enough images
    while len(available_images) < num_images:
        available_images.extend(available_images)
    
    # Return random subset
    return random.sample(available_images, min(num_images, len(available_images)))

def download_image(url: str) -> Optional[Image.Image]:
    """
    Download an image from a URL
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, stream=True, timeout=5, headers=headers)
        response.raise_for_status()
        return Image.open(io.BytesIO(response.content))
    except Exception as e:
        logger.error(f"Error downloading image from {url}: {str(e)}")
        return None

def create_outfit_collage(items, width=800, height=600):
    """
    Create a collage of outfit items with clickable areas
    Returns a dictionary with 'image' (base64 encoded) and 'map' (clickable areas)
    """
    try:
        # Create a white canvas
        collage = Image.new('RGBA', (width, height), (255, 255, 255, 255))
        draw = ImageDraw.Draw(collage)
        click_map = []
        
        # Skip if no items
        if not items:
            logger.warning("No items provided for collage creation")
            buffered = BytesIO()
            collage.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            return {"image": img_str, "map": []}
        
        # Define optimal positions for different categories
        # Each position is (x_center, y_center, max_width, max_height)
        category_positions = {
            "Top": (width // 2, height // 4, width // 2, height // 3),          # Center top
            "Bottom": (width * 3 // 4, height // 2, width // 3, height // 3),   # Right middle
            "Dress": (width // 2, height // 2, width // 2, height * 3 // 5),    # Center
            "Shoes": (width // 2, height * 4 // 5, width // 3, height // 6),    # Bottom center
            "Accessories": (width * 3 // 4, height // 4, width // 4, height // 5), # Top right
            "Outerwear": (width // 4, height // 2, width // 3, height // 2),    # Left middle
            "Bag": (width * 3 // 4, height * 3 // 5, width // 5, height // 5),  # Right bottom
            "Jewelry": (width * 3 // 4, height // 5, width // 6, height // 6),  # Top right corner
            "Hat": (width // 2, height // 7, width // 6, height // 6),          # Top center
        }
        
        # Default positions if we have items without specific category matching
        default_positions = [
            (width // 4, height // 4, width // 3, height // 3),      # Top left
            (width * 3 // 4, height // 4, width // 3, height // 3),   # Top right
            (width // 4, height * 3 // 4, width // 3, height // 3),   # Bottom left
            (width * 3 // 4, height * 3 // 4, width // 3, height // 3), # Bottom right
            (width // 2, height // 2, width // 3, height // 3),       # Center
        ]
        
        # Map generic categories to our specific positions
        category_mapping = {
            "tops": "Top",
            "bottoms": "Bottom",
            "dresses": "Dress",
            "shoes": "Shoes",
            "accessories": "Accessories",
            "outerwear": "Outerwear", 
            "bags": "Bag",
            "jewelry": "Jewelry",
            "hats": "Hat"
        }
        
        # Track which positions are used
        used_positions = set()
        default_position_index = 0
        
        # Function to get position for a category
        def get_position_for_category(category):
            # Normalize category name
            category_lower = category.lower()
            
            # Try direct match first
            if category in category_positions:
                pos = category_positions[category]
                used_positions.add(category)
                return pos
                
            # Try mapped category
            for key, value in category_mapping.items():
                if key == category_lower or key in category_lower or category_lower in key:
                    if value not in used_positions:
                        used_positions.add(value)
                        return category_positions[value]
            
            # Use default position if no match
            nonlocal default_position_index
            if default_position_index < len(default_positions):
                pos = default_positions[default_position_index]
                default_position_index += 1
                return pos
            
            # If all positions are used, just return center
            return (width // 2, height // 2, width // 3, height // 3)
        
        # Sort items to ensure consistent display (shoes at bottom, etc.)
        display_order = ["Hat", "Accessories", "Jewelry", "Top", "Outerwear", "Dress", "Bottom", "Bag", "Shoes"]
        
        # Create a sorted list based on category priority
        def get_category_priority(item):
            category = item.get("category", "").capitalize()
            
            # Check for exact match
            for i, cat in enumerate(display_order):
                if cat == category:
                    return i
                    
            # Check for partial match
            for i, cat in enumerate(display_order):
                if cat.lower() in category.lower() or category.lower() in cat.lower():
                    return i
                    
            # Default to middle priority if no match
            return len(display_order) // 2
        
        # Sort items by display priority
        sorted_items = sorted(items, key=get_category_priority)
        
        # Draw each item on the collage
        for item in sorted_items:
            try:
                image_url = item.get("image_url")
                category = item.get("category", "Unknown")
                source_url = item.get("source_url", "#")
                
                if not image_url:
                    continue
                
                # Get position for this category
                x_center, y_center, max_width, max_height = get_position_for_category(category)
                
                # Download image
                try:
                    # Attempt to download the image with a timeout
                    response = requests.get(image_url, timeout=5)
                    if response.status_code == 200:
                        img = Image.open(BytesIO(response.content))
                    else:
                        logger.warning(f"Failed to download image: {image_url}, status: {response.status_code}")
                        continue
                except Exception as e:
                    logger.warning(f"Error loading image {image_url}: {str(e)}")
                    continue
                
                # Convert RGBA images to RGB if needed
                if img.mode == 'RGBA':
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3])
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize image to fit in the allocated space while maintaining aspect ratio
                img_width, img_height = img.size
                aspect_ratio = img_width / img_height
                
                # Calculate dimensions to fit within max bounds
                if aspect_ratio > 1:  # Width > Height
                    new_width = min(max_width, img_width)
                    new_height = int(new_width / aspect_ratio)
                    if new_height > max_height:
                        new_height = max_height
                        new_width = int(new_height * aspect_ratio)
                else:  # Height >= Width
                    new_height = min(max_height, img_height)
                    new_width = int(new_height * aspect_ratio)
                    if new_width > max_width:
                        new_width = max_width
                        new_height = int(new_width / aspect_ratio)
                
                # Resize the image
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Calculate position to paste the image (centered at the specified position)
                x1 = x_center - new_width // 2
                y1 = y_center - new_height // 2
                
                # Paste the image onto the collage
                collage.paste(img, (x1, y1))
                
                # Add a subtle border around the image
                border_color = (200, 200, 200, 255)  # Light gray
                draw.rectangle([x1, y1, x1 + new_width - 1, y1 + new_height - 1], outline=border_color, width=2)
                
                # Add a label for the category
                font_size = 18
                try:
                    font = ImageFont.truetype("Arial.ttf", font_size)
                except Exception:
                    font = ImageFont.load_default()
                
                # Draw semi-transparent label background
                label_text = category.upper()
                label_width, label_height = draw.textsize(label_text, font=font) if hasattr(draw, 'textsize') else (font_size * len(label_text) * 0.6, font_size * 1.2)
                label_x = x1 + (new_width - label_width) // 2
                label_y = y1 + new_height - label_height - 10
                
                # Draw rounded rectangle for label
                draw.rectangle([label_x - 5, label_y - 5, label_x + label_width + 5, label_y + label_height + 5], 
                              fill=(0, 0, 0, 128), outline=(255, 255, 255, 200), width=1)
                
                # Draw text
                text_color = (255, 255, 255, 255)  # White
                draw.text((label_x, label_y), label_text, font=font, fill=text_color)
                
                # Add to click map
                click_map.append({
                    "coords": [x1, y1, x1 + new_width, y1 + new_height],
                    "category": category,
                    "url": source_url
                })
                
            except Exception as e:
                logger.warning(f"Error adding item to collage: {str(e)}")
                continue
        
        # Convert the image to base64
        buffered = BytesIO()
        collage.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return {"image": img_str, "map": click_map}
        
    except Exception as e:
        logger.error(f"Error creating outfit collage: {str(e)}")
        # Return empty image
        return {"image": "", "map": []} 