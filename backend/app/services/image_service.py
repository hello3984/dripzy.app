import os
import io
import requests
import base64
import logging
import random
import re
from PIL import Image
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get Google API credentials
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

def get_images_from_web(query: str, num_images: int = 5, category: str = None) -> List[Dict[str, str]]:
    """
    Scrape images from the web without using Google API
    Returns a list of dicts with 'image_url' and 'source_url' keys
    """
    try:
        # Format search query
        search_query = f"{query} {category if category else ''} fashion outfit"
        encoded_query = quote_plus(search_query)
        
        # We'll try multiple sources to ensure we get enough results
        image_results = []
        
        # Try Pinterest first (good for fashion)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Try Bing image search
        bing_url = f"https://www.bing.com/images/search?q={encoded_query}&form=HDRSC2&first=1"
        try:
            response = requests.get(bing_url, headers=headers, timeout=8)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # Find image elements (specific to Bing's structure)
                img_tags = soup.find_all('img', {'class': 'mimg'})
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
        except Exception as e:
            logger.warning(f"Error scraping Bing: {str(e)}")
        
        # Try Duck Duck Go as a backup
        ddg_url = f"https://duckduckgo.com/?q={encoded_query}&iax=images&ia=images"
        try:
            response = requests.get(ddg_url, headers=headers, timeout=8)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # Extract image URLs from the page source
                # DuckDuckGo dynamically loads images with JavaScript, but we can find some in the initial HTML
                script_tags = soup.find_all('script')
                for script in script_tags:
                    if script.string and 'vqd' in str(script.string):
                        # Look for image URLs in the script content
                        urls = re.findall(r'(https://[^"\']+\.(?:jpg|jpeg|png|webp))', str(script.string))
                        for img_url in urls:
                            image_results.append({
                                'image_url': img_url,
                                'source_url': f"https://duckduckgo.com/?q={encoded_query}&iax=images&ia=images"
                            })
        except Exception as e:
            logger.warning(f"Error scraping DuckDuckGo: {str(e)}")
            
        # If we didn't get enough images, try Unsplash (which has high-quality fashion images)
        if len(image_results) < num_images:
            unsplash_url = f"https://unsplash.com/s/photos/{encoded_query.replace('+', '-')}"
            try:
                response = requests.get(unsplash_url, headers=headers, timeout=8)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    img_tags = soup.find_all('img')
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
            except Exception as e:
                logger.warning(f"Error scraping Unsplash: {str(e)}")
        
        # Unique URLs only - use dict to deduplicate
        unique_results = {}
        for result in image_results:
            img_url = result['image_url']
            if img_url not in unique_results:
                unique_results[img_url] = result
        
        image_results = list(unique_results.values())
        
        # Filter out small images (likely thumbnails or icons)
        filtered_results = []
        for result in image_results:
            url = result['image_url']
            if not ('icon' in url.lower() or 'thumbnail' in url.lower() or 'logo' in url.lower()):
                if url.endswith(('.jpg', '.jpeg', '.png', '.webp')) or 'images' in url.lower():
                    filtered_results.append(result)
        
        if not filtered_results:
            logger.warning(f"No images found for query: {search_query}")
            return get_mock_images(category, num_images)
            
        # Return a random subset of the results
        if len(filtered_results) > num_images:
            filtered_results = random.sample(filtered_results, num_images)
        
        return filtered_results
    
    except Exception as e:
        logger.error(f"Error searching for images: {str(e)}")
        return get_mock_images(category, num_images)

# Alias the function to maintain compatibility with existing code
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

def create_outfit_collage(outfit_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Create a collage from outfit items and return as base64 encoded string
    with clickable areas for each item
    """
    try:
        # Download images
        images = []
        image_map = []  # To store clickable areas
        
        for item in outfit_items:
            if "image_url" in item and item["image_url"]:
                img = download_image(item["image_url"])
                if img:
                    images.append((img, item.get("category", "Unknown")))
                    # Keep track of the source URL for each image
                    image_map.append({
                        "category": item.get("category", "Unknown"),
                        "url": item.get("source_url", "#")
                    })
        
        if not images:
            logger.warning("No valid images to create collage")
            return {"image": None, "map": []}
        
        # Calculate collage dimensions
        width = 1000
        height = 1200
        collage = Image.new('RGBA', (width, height), (255, 255, 255, 0))
        
        # Define positions for different categories
        category_positions = {
            "Top": (50, 50, 450, 450),
            "Dress": (50, 50, 450, 700),
            "Bottom": (50, 500, 450, 900),
            "Shoes": (500, 700, 900, 1100),
            "Accessory": (500, 50, 900, 450),
            "Outerwear": (500, 500, 900, 650),
            "Unknown": (250, 500, 650, 900)
        }
        
        # Map for placing additional items of the same category
        additional_positions = {
            "Top": [(500, 500, 900, 900)],
            "Bottom": [(500, 500, 900, 900)],
            "Accessory": [(700, 500, 950, 750), (250, 700, 500, 950)],
            "Shoes": [(50, 700, 450, 1100)],
            "Outerwear": [(50, 500, 450, 900)]
        }
        
        # Track used positions and categories
        used_positions = set()
        used_categories = set()
        image_map_with_coords = []  # Store coordinates for clickable areas
        
        # Place images in collage based on category
        for i, (img, category) in enumerate(images):
            if category in used_categories and category in additional_positions and additional_positions[category]:
                # Use alternative position for additional items of the same category
                position = additional_positions[category].pop(0)
            elif category in category_positions and category not in used_categories:
                # Use main position for the category
                position = category_positions[category]
                used_categories.add(category)
            else:
                # Find any unused position
                available_positions = [pos for cat, pos in category_positions.items() if cat not in used_categories]
                if not available_positions:
                    # If all category positions are used, try additional positions
                    for cat, positions in additional_positions.items():
                        if positions:
                            position = positions.pop(0)
                            break
                    else:
                        # Skip if no positions available
                        continue
                else:
                    position = available_positions[0]
                    used_categories.add(next(cat for cat, pos in category_positions.items() if pos == position))
            
            # Remember this position is used
            position_key = f"{position[0]},{position[1]}"
            if position_key in used_positions:
                continue
            used_positions.add(position_key)
            
            # Calculate dimensions
            width_pos = position[2] - position[0]
            height_pos = position[3] - position[1]
            
            # Resize and maintain aspect ratio
            img_width, img_height = img.size
            ratio = min(width_pos / img_width, height_pos / img_height)
            new_size = (int(img_width * ratio), int(img_height * ratio))
            
            # Resize image
            img_resized = img.resize(new_size, Image.LANCZOS)
            
            # Center image in position
            x_offset = position[0] + (width_pos - new_size[0]) // 2
            y_offset = position[1] + (height_pos - new_size[1]) // 2
            
            # Create a white background for transparent images
            if img_resized.mode == 'RGBA':
                background = Image.new('RGBA', new_size, (255, 255, 255, 255))
                background.paste(img_resized, (0, 0), img_resized)
                img_resized = background
            
            # Paste image onto collage
            collage.paste(img_resized, (x_offset, y_offset))
            
            # Save the coordinates for the clickable area
            if i < len(image_map):
                image_map_with_coords.append({
                    "category": image_map[i]["category"],
                    "url": image_map[i]["url"],
                    "coords": {
                        "x1": x_offset, 
                        "y1": y_offset,
                        "x2": x_offset + new_size[0],
                        "y2": y_offset + new_size[1]
                    }
                })
        
        # Save collage to bytes buffer
        buffer = io.BytesIO()
        collage.save(buffer, format="PNG")
        
        # Convert to base64
        img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return {
            "image": f"data:image/png;base64,{img_str}",
            "map": image_map_with_coords
        }
        
    except Exception as e:
        logger.error(f"Error creating outfit collage: {str(e)}")
        return {"image": None, "map": []} 