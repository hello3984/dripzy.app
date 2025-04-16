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
    try:
        # Enhance query with category and fashion terms
        if category and category not in query:
            query = f"{query} {category}"
        
        if "fashion" not in query.lower():
            query = f"{query} fashion"
            
        if "festival" not in query.lower() and "coachella" not in query.lower():
            query = f"{query} festival"
            
        print(f"Enhanced image search query: {query}")
        
        # Try Bing images first (usually most relevant)
        bing_results = get_bing_images(query, num_images * 2) or [] # Ensure list
        
        # Try Unsplash as backup for high-quality images
        unsplash_results = []
        if len(bing_results) < num_images:
            unsplash_results = get_unsplash_images(query, num_images * 2) or [] # Ensure list
            
        # Combine and filter results
        all_results = bing_results + unsplash_results
        
        # Remove duplicates and filter low quality images
        filtered_results = []
        seen_urls = set()
        
        for result in all_results:
            url = result.get('image_url', '')
            
            # Skip if we've seen this URL or it's empty
            if not url or url in seen_urls:
                continue
                
            # Skip icons, thumbnails, placeholders, etc.
            if any(term in url.lower() for term in ['icon', 'thumbnail', 'logo', 'placeholder']):
                continue
                
            # Skip very small images
            if 'width=' in url and 'height=' in url:
                try:
                    width_match = re.search(r'width=(\d+)', url)
                    height_match = re.search(r'height=(\d+)', url)
                    if width_match and height_match:
                        width = int(width_match.group(1))
                        height = int(height_match.group(1))
                        if width < 200 or height < 200:
                            continue
                except:
                    pass
            
            seen_urls.add(url)
            filtered_results.append(result)
            
            # Break early if we have enough results
            if len(filtered_results) >= num_images:
                break
                
        # Return filtered results, or placeholders if none found
        if filtered_results:
            return filtered_results[:num_images]
        else:
            print(f"Warning: No suitable images found for query: {query}")
            placeholders = []
            for i in range(num_images):
                placeholders.append({
                    "image_url": f"https://via.placeholder.com/400x600?text={category}+Item",
                    "source_url": "#"
                })
            return placeholders
            
    except Exception as e:
        print(f"Error in get_images_from_web: {str(e)}")
        # Return placeholders on error
        placeholders = []
        for i in range(num_images):
            placeholders.append({
                "image_url": f"https://via.placeholder.com/400x600?text=Error",
                "source_url": "#"
            })
        return placeholders

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
    if not url or not url.startswith('http'):
        logger.error(f"Invalid URL provided for image download: {url}")
        return None
        
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # Increased timeout slightly
        response = requests.get(url, stream=True, timeout=10, headers=headers)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        
        # Check content type if possible
        content_type = response.headers.get('content-type')
        if content_type and not content_type.startswith('image/'):
            logger.warning(f"URL did not return an image type (Content-Type: {content_type}): {url}")
            return None
            
        # Try opening the image
        try:
            img = Image.open(io.BytesIO(response.content))
            return img
        except Exception as img_err:
            logger.error(f"Error opening image content from {url}: {str(img_err)}")
            return None
            
    except requests.exceptions.Timeout:
        logger.error(f"Timeout error downloading image from {url}")
        return None
    except requests.exceptions.RequestException as e:
        # Catch other request errors (ConnectionError, HTTPError, etc.)
        logger.error(f"Error downloading image from {url}: {str(e)}")
        return None
    except Exception as e:
        # Catch any other unexpected errors
        logger.error(f"Unexpected error during image download from {url}: {str(e)}", exc_info=True)
        return None

def create_outfit_collage(items, width=800, height=800):
    """
    Create a collage of outfit items with clickable areas
    Returns a dictionary with 'image' (base64 encoded) and 'map' (clickable areas)
    """
    try:
        # Create a white canvas with subtle background texture
        collage = Image.new('RGBA', (width, height), (252, 252, 252, 255))
        draw = ImageDraw.Draw(collage)
        
        # Add a subtle gradient background
        for y in range(height):
            color = (252, 252, 252, 255)
            if y < height/4:  # Top gradient
                color = (245, 245, 250, 255)
            elif y > height*3/4:  # Bottom gradient
                color = (250, 248, 245, 255)
            draw.line([(0, y), (width, y)], fill=color)
            
        click_map = []
        
        # Skip if no items
        if not items:
            logger.warning("No items provided for collage creation")
            buffered = BytesIO()
            collage.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            return {"image": img_str, "map": []}
        
        # Define optimal positions for different categories specifically for festival outfits
        # Format: (x_center, y_center, max_width, max_height)
        category_positions = {
            "Top": (width // 2, height // 4, width // 2, height // 3),          # Center top
            "Bottom": (width * 3 // 4, height // 2, width // 2.5, height // 2.5),   # Right middle
            "Dress": (width // 2, height // 2, width // 2, height * 2 // 3),    # Center
            "Shoes": (width // 2, height * 4 // 5, width // 3, height // 6),    # Bottom center
            "Accessories": (width * 3 // 4, height // 4, width // 4, height // 5),  # Top right
            "Outerwear": (width // 4, height // 2, width // 2.5, height // 2),  # Left middle
            "Bag": (width * 3 // 4, height * 3 // 5, width // 5, height // 5),  # Right bottom
            "Jewelry": (width * 4 // 5, height // 5, width // 8, height // 8),  # Top right corner
            "Hat": (width // 4, height // 6, width // 6, height // 6),          # Top left
            "Sunglasses": (width * 3 // 4, height // 3, width // 6, height // 8),  # Right top
        }
        
        # Convert all floating point values to integers in category_positions
        for category, (x, y, w, h) in category_positions.items():
            category_positions[category] = (int(x), int(y), int(w), int(h))
        
        # Fallback positions if specific category position isn't available
        default_positions = [
            (width // 4, height // 3, width // 3, height // 3),
            (width * 3 // 4, height // 3, width // 3, height // 3),
            (width // 4, height * 2 // 3, width // 3, height // 3),
            (width * 3 // 4, height * 2 // 3, width // 3, height // 3),
            (width // 2, height // 2, width // 3, height // 3),
        ]
        
        # Convert all floating point values to integers in default_positions
        default_positions = [(int(x), int(y), int(w), int(h)) for x, y, w, h in default_positions]
        
        # Map generic categories to our specific positions
        category_mapping = {
            "tops": "Top",
            "tee": "Top", 
            "tshirt": "Top",
            "shirt": "Top",
            "tank": "Top",
            "blouse": "Top",
            "bottoms": "Bottom",
            "jean": "Bottom",
            "jeans": "Bottom",
            "pants": "Bottom",
            "shorts": "Bottom",
            "skirt": "Bottom",
            "dresses": "Dress",
            "dress": "Dress",
            "shoes": "Shoes",
            "sneakers": "Shoes",
            "boots": "Shoes",
            "sandals": "Shoes",
            "accessories": "Accessories",
            "necklace": "Jewelry",
            "earrings": "Jewelry",
            "bracelet": "Jewelry",
            "jewelry": "Jewelry",
            "outerwear": "Outerwear",
            "jacket": "Outerwear",
            "kimono": "Outerwear",
            "cardigan": "Outerwear",
            "bag": "Bag",
            "purse": "Bag",
            "handbag": "Bag",
            "crossbody": "Bag",
            "sunglass": "Sunglasses",
            "glasses": "Sunglasses",
            "hat": "Hat",
            "cap": "Hat",
            "fedora": "Hat",
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
                if category not in used_positions:
                    used_positions.add(category)
                    return category_positions[category]
                
            # Try specific subcategory matches
            for key, value in category_mapping.items():
                if key in category_lower:
                    if value not in used_positions:
                        used_positions.add(value)
                        return category_positions[value]
            
            # Try generic category match
            for base_category in ["Top", "Bottom", "Dress", "Shoes", "Accessories", "Outerwear"]:
                if base_category.lower() in category_lower or category_lower in base_category.lower():
                    if base_category not in used_positions:
                        used_positions.add(base_category)
                        return category_positions[base_category]
            
            # Use default position if no match
            nonlocal default_position_index
            if default_position_index < len(default_positions):
                pos = default_positions[default_position_index]
                default_position_index += 1
                return pos
            
            # If all positions are used, return center
            return (width // 2, height // 2, width // 3, height // 3)
        
        # Sort items to ensure consistent display (top layer items last)
        display_order = [
            "Shoes", "Bottom", "Dress", "Top", "Outerwear", 
            "Bag", "Hat", "Sunglasses", "Accessories", "Jewelry"
        ]
        
        # Create a sorted list based on category priority
        def get_category_priority(item):
            category = item.get("category", "").capitalize()
            
            # Check for specific category matches first
            for key, value in category_mapping.items():
                if key in category.lower():
                    for i, cat in enumerate(display_order):
                        if cat == value:
                            return i
            
            # Then check for direct matches with display order
            for i, cat in enumerate(display_order):
                if cat == category:
                    return i
                    
            # Then check for partial matches
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
                    response = requests.get(image_url, timeout=8)
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
                img = img.resize((int(new_width), int(new_height)), Image.Resampling.LANCZOS)
                
                # Calculate position to paste the image (centered at the specified position)
                x1 = int(x_center - new_width // 2)
                y1 = int(y_center - new_height // 2)
                
                # Paste the image onto the collage
                collage.paste(img, (x1, y1))
                
                # Add a subtle shadow (draw slight darker rectangle underneath)
                shadow_offset = 6
                shadow_color = (230, 230, 230, 255)
                draw.rectangle([
                    int(x1+shadow_offset), 
                    int(y1+shadow_offset), 
                    int(x1+new_width+shadow_offset-1), 
                    int(y1+new_height+shadow_offset-1)
                ], fill=shadow_color, outline=None)
                
                # Paste the image again over the shadow
                collage.paste(img, (x1, y1))
                
                # Add a subtle border around the image
                border_color = (220, 220, 220, 255)  # Light gray
                draw.rectangle([
                    x1, 
                    y1, 
                    int(x1 + new_width - 1), 
                    int(y1 + new_height - 1)
                ], outline=border_color, width=1)
                
                # Add to click map
                click_map.append({
                    "coords": [x1, y1, int(x1 + new_width), int(y1 + new_height)],
                    "category": category,
                    "url": source_url
                })
                
            except Exception as e:
                logger.warning(f"Error adding item to collage: {str(e)}")
                continue
        
        # Apply a subtle vignette effect
        mask = Image.new('L', (width, height), 255)
        for y in range(height):
            for x in range(width):
                # Calculate distance from center
                distance = ((x - width/2)**2 + (y - height/2)**2)**0.5
                # Calculate radius from center to corner
                max_distance = ((width/2)**2 + (height/2)**2)**0.5
                # Set mask value based on distance ratio
                if distance > max_distance * 0.7:  # Start vignette at 70% from center
                    ratio = (distance - max_distance * 0.7) / (max_distance * 0.3)
                    mask.putpixel((x, y), int(255 * (1 - ratio * 0.2)))  # Slight darkening
        
        # Apply the vignette mask
        alpha = Image.new('L', collage.size, 255)
        alpha.paste(mask, (0, 0))
        collage.putalpha(alpha)
        
        # Convert the image to base64
        buffered = BytesIO()
        collage.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return {"image": img_str, "map": click_map}
        
    except Exception as e:
        logger.error(f"Error creating outfit collage: {str(e)}")
        # Return empty image
        return {"image": "", "map": []} 