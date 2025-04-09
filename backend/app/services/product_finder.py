import requests
from bs4 import BeautifulSoup
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_real_product_nordstrom(item_details: dict) -> dict | None:
    """
    Attempts to find a matching product on Nordstrom based on item details.

    Args:
        item_details: A dictionary containing keys like 'description', 
                      'keywords', 'color', 'category'.

    Returns:
        A dictionary with 'name', 'brand', 'price', 'image_url', 'product_url' 
        if a product is found, otherwise None.
    """
    description = item_details.get('description', '')
    keywords = item_details.get('keywords', [])
    color = item_details.get('color', '')
    category = item_details.get('category', '') # Consider mapping category to Nordstrom departments

    # --- 1. Construct Search Query ---
    # Combine details into a search term appropriate for Nordstrom
    search_term = f"{color} {description} {' '.join(keywords)}" 
    logger.info(f"Searching Nordstrom for: {search_term}")

    # --- 2. Construct Nordstrom Search URL ---
    # Base URL might change, needs verification
    base_url = "https://www.nordstrom.com/browse/search" 
    params = {'keyword': search_term}

    # --- 3. Make HTTP Request ---
    headers = {
        # Set a realistic User-Agent to reduce chances of being blocked immediately
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(base_url, params=params, headers=headers, timeout=10) # Added timeout
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        logger.info(f"Nordstrom search URL: {response.url}")
        logger.info(f"Nordstrom response status: {response.status_code}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching Nordstrom search results for '{search_term}': {e}")
        return None

    # --- 4. Parse HTML with BeautifulSoup ---
    soup = BeautifulSoup(response.text, 'html.parser')

    # --- 5. Extract Product Information ---
    # !!! IMPORTANT: The selectors below are educated GUESSES based on common patterns 
    # !!! and WILL LIKELY NEED ADJUSTMENT after inspecting the live Nordstrom site.
    try:
        # Find the container for the first product result (GUESS)
        # Looking for a div/article that seems to represent a product tile
        product_container = soup.find(['div', 'article'], class_=lambda x: x and ('product' in x or 'tile' in x)) 
        
        if not product_container:
            logger.warning(f"No product container found using guessed selectors on Nordstrom for: {search_term}")
            # Optional: Log soup.prettify() here to help debug HTML structure
            # logger.debug(soup.prettify())
            return None

        # Extract Product Name (GUESS)
        # Looking for h2/h3 or link text containing 'title' or 'name'
        name_element = product_container.find(['h2', 'h3', 'a'], class_=lambda x: x and ('title' in x or 'name' in x))
        # Fallback: Try finding any link text within the container if specific class fails
        if not name_element:
            name_link = product_container.find('a')
            if name_link:
                 name = name_link.text.strip()
            else: 
                name = "Name Not Found"
        else:
            name = name_element.text.strip()

        # Extract Product Price (GUESS)
        # Looking for span/div containing 'price'
        price_element = product_container.find(['span', 'div'], class_=lambda x: x and 'price' in x)
        price_str = "0"
        if price_element:
            # Attempt to find the most specific price text within the element
            price_text_element = price_element.find(string=re.compile(r'\$\d')) # Find text node containing '$' followed by a digit
            if price_text_element:
                 price_str = price_text_element.strip()
            else: # Fallback to element's text if specific node not found
                price_str = price_element.text.strip()
        
        # Clean price string (needs improvement for ranges, sales etc.)
        try:
             # More robust cleaning: remove currency, commas, take first part if range/sale
             cleaned_price_str = re.sub(r'[^\d.,-]', '', price_str).split('-')[0].split(',')[0].strip()
             price = float(cleaned_price_str)
        except ValueError:
            logger.warning(f"Could not parse price string: '{price_str}'")
            price = 0.0 # Default to 0 if parsing fails

        # Extract Product Image URL (GUESS)
        # Looking for img tag, check src, data-src, data-srcset
        image_element = product_container.find('img') 
        image_url = None
        if image_element:
            image_url = image_element.get('src') or image_element.get('data-src')
            # Basic check if URL is relative
            if image_url and image_url.startswith('/'):
                image_url = f"https://www.nordstrom.com{image_url}"
            # TODO: Handle srcset potentially

        # Extract Product URL (GUESS)
        # Looking for the main link 'a' tag within the container
        link_element = product_container.find('a') 
        product_url = None
        if link_element:
            product_url_relative = link_element.get('href')
            if product_url_relative:
                 # Ensure it's a plausible product link (starts with /s/ or /c/ typically)
                 if product_url_relative.startswith(('/s/', '/c/')):
                      product_url = f"https://www.nordstrom.com{product_url_relative}"
                 elif product_url_relative.startswith('http'): # Handle absolute URLs if present
                      product_url = product_url_relative

        # Extract Brand (GUESS)
        # Looking for element with 'brand' in class, or parse from name?
        brand_element = product_container.find(['span', 'div'], class_=lambda x: x and 'brand' in x)
        brand = "Brand Not Found"
        if brand_element:
            brand = brand_element.text.strip()
        else:
            # Very basic attempt to extract brand from name (assuming 'BRAND Name of Product')
            if name != "Name Not Found" and ' ' in name:
                 # Simple split might work for some cases, but unreliable
                 potential_brand = name.split(' ')[0] 
                 # Add checks if this looks like a real brand (e.g., capitalized?)
                 brand = potential_brand # Placeholder assignment

        # Log extracted data
        logger.info(f"GUESS Extracted from Nordstrom: Name='{name}', Brand='{brand}', Price='{price}', URL='{product_url}', ImageURL='{image_url}'")

        # Return structured data if essential parts seem valid
        if name != "Name Not Found" and price > 0 and product_url and image_url:
            return {
                "name": name,
                "brand": brand, 
                "price": price,
                "image_url": image_url,
                "product_url": product_url,
                "source": "Nordstrom" 
            }
        else:
            logger.warning(f"Could not extract all necessary details using guessed selectors from Nordstrom for: {search_term}")
            return None

    except Exception as e:
        logger.error(f"Error parsing Nordstrom HTML for '{search_term}': {e}", exc_info=True)
        return None

# --- Placeholder for other retailers ---
# def find_real_product_zara(item_details: dict) -> dict | None:
#     pass 

# --- Main function to try different retailers ---
# def find_real_product(item_details: dict) -> dict | None:
#     """Tries to find a product by attempting different retailers."""
#     
#     # Try Nordstrom first
#     product = find_real_product_nordstrom(item_details)
#     if product:
#         return product
#         
#     # Add attempts for other retailers here later
#     # product = find_real_product_zara(item_details)
#     # if product:
#     #     return product
#         
#     logger.warning(f"Could not find real product for details: {item_details}")
#     return None 