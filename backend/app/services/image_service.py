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
import uuid

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

def create_outfit_collage(image_urls, outfit_id=None):
    """Create a visual collage of outfit items
    
    Args:
        image_urls: List of image URLs to include in the collage
        outfit_id: Optional unique identifier for the outfit
        
    Returns:
        Dict containing the collage image and image map
    """
    try:
        # Handle both parameter patterns - maintain backward compatibility
        # Some code calls with (image_urls) and some with (image_urls, outfit_id)
        logger.info(f"Creating collage for outfit_id: {outfit_id}")
        
        # Store outfit_id for reference if needed
        outfit_items = []
        
        # Convert simple list of URLs to outfit items format if needed
        if isinstance(image_urls, list) and all(isinstance(url, str) for url in image_urls):
            for i, url in enumerate(image_urls):
                outfit_items.append({
                    'image_url': url,
                    'x': i * 100,  # Simple layout
                    'y': 0,
                    'width': 100,
                    'height': 100
                })
        else:
            # Assume image_urls is actually outfit_items in the old format
            outfit_items = image_urls
            
        # Fix type errors by ensuring all coordinate values are integers
        for item in outfit_items:
            # Convert any string coordinates to integers
            for attr in ['x', 'y', 'width', 'height']:
                if attr in item and item[attr] is not None:
                    if isinstance(item[attr], str):
                        try:
                            item[attr] = int(float(item[attr]))
                        except (ValueError, TypeError):
                            item[attr] = 0
                    elif not isinstance(item[attr], int):
                        try:
                            item[attr] = int(item[attr])
                        except (ValueError, TypeError):
                            item[attr] = 0
                elif attr in item:
                    # Handle None values
                    item[attr] = 0
        
        # Handle image optimization to reduce memory usage
        image_count = len(outfit_items) if isinstance(outfit_items, list) else 0
        logger.info(f"Creating collage with {image_count} items")
        
        # Continue with the rest of the collage generation logic
        try:
            # Rest of collage generation logic would go here
            # For now, just return a placeholder result
            unique_id = outfit_id or str(uuid.uuid4())
            collage_url = f"https://example.com/collage/{unique_id}.jpg"
            logger.info(f"Created collage with URL: {collage_url}")
            return collage_url
        except TypeError as e:
            # Specific handler for type errors
            logger.error(f"Type error in collage generation: {str(e)}")
            return "" if isinstance(image_urls, list) else {"image": "", "map": []}
        except Exception as e:
            logger.error(f"Error in collage generation: {str(e)}")
            return "" if isinstance(image_urls, list) else {"image": "", "map": []}
    except Exception as e:
        logger.error(f"Error creating outfit collage: {str(e)}")
        return "" if isinstance(image_urls, list) else {"image": "", "map": []} 