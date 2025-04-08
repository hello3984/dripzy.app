import requests
from bs4 import BeautifulSoup
import json
import time
import random
import os
from typing import List, Dict, Any, Optional

class ProductScraper:
    """Service to scrape or fetch products from various sources based on search criteria"""
    
    def __init__(self):
        """Initialize with API keys if needed"""
        # Optional: Add API keys for services like Shopify, etc.
        self.rapid_api_key = os.getenv("RAPID_API_KEY", "")
        
        # Popular premium/designer brands by category
        self.category_brands = {
            "top": ["Zara", "H&M", "Free People", "Urban Outfitters", "Topshop", "Reformation", "Aritzia", "Lands' End"],
            "bottom": ["Levi's", "Gap", "J.Crew", "Madewell", "PAIGE", "Re/Done", "AGOLDE", "Citizens of Humanity"],
            "dress": ["Reformation", "Anthropologie", "ASOS", "& Other Stories", "Mango", "For Love & Lemons", "Free People"],
            "shoes": ["Steve Madden", "Aldo", "Nike", "Adidas", "Vans", "Gianvito Rossi", "Stuart Weitzman", "Jimmy Choo"],
            "accessory": ["Madewell", "Urban Outfitters", "Aritzia", "Anthropologie", "J.Crew", "Mansur Gavriel", "Loewe", "Jacquemus"],
            "outerwear": ["Zara", "H&M", "ASOS", "The North Face", "Patagonia", "Canada Goose", "PAIGE", "J.Crew"]
        }
        
        # Festival specific brands by category
        self.festival_brands = {
            "top": ["Free People", "Urban Outfitters", "For Love & Lemons", "Spell", "Nasty Gal", "Revolve", "ASOS"],
            "bottom": ["Levi's", "One Teaspoon", "Free People", "Urban Outfitters", "AGOLDE", "Re/Done"],
            "dress": ["Free People", "For Love & Lemons", "Spell", "Anthropologie", "Reformation", "ASOS"],
            "shoes": ["Dr. Martens", "Steve Madden", "Jeffrey Campbell", "Freebird", "Sam Edelman", "Birkenstock"],
            "accessory": ["Free People", "Urban Outfitters", "Vanessa Mooney", "Lack of Color", "Etsy", "ASOS"],
            "outerwear": ["Free People", "BlankNYC", "Urban Outfitters", "ASOS", "Levi's"]
        }
        
    def search_products(self, keywords: str, category: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for products matching keywords and category
        Returns a list of product dictionaries
        """
        print(f"Searching for products: {keywords} in category {category}")
        
        # First try to use a real API if possible
        if self.rapid_api_key:
            try:
                # Try to use an e-commerce API first
                products = self._search_rapid_api(keywords, category, limit)
                if products and len(products) > 0:
                    return products
            except Exception as e:
                print(f"API search failed: {str(e)}")
        
        # If API search fails or no API key, use fallback methods
        
        # First, try scraping if this is a development environment
        # Note: In production, you'd want to use proper APIs instead of scraping
        try:
            products = self._create_simulated_products(keywords, category, limit)
            if products and len(products) > 0:
                return products
        except Exception as e:
            print(f"Simulated product search failed: {str(e)}")
            
        # If all fails, return empty list
        return []
    
    def _search_rapid_api(self, keywords: str, category: str, limit: int) -> List[Dict[str, Any]]:
        """Search products using RapidAPI e-commerce APIs"""
        if not self.rapid_api_key:
            return []
            
        # Choose which API to use based on category
        if category.lower() in ["dress", "dresses", "gown", "gowns"]:
            return self._search_asos_api(keywords, category, limit)
        elif category.lower() in ["shoes", "footwear", "heels", "boots", "sneakers"]:
            return self._search_zappos_api(keywords, category, limit)
        else:
            return self._search_shopify_api(keywords, category, limit)
    
    def _search_shopify_api(self, keywords: str, category: str, limit: int) -> List[Dict[str, Any]]:
        """Search products using Shopify API"""
        # This is a placeholder. In a real implementation, you would call the Shopify API
        return []
        
    def _search_asos_api(self, keywords: str, category: str, limit: int) -> List[Dict[str, Any]]:
        """Search products using ASOS API"""
        # This is a placeholder. In a real implementation, you would call the ASOS API
        return []
        
    def _search_zappos_api(self, keywords: str, category: str, limit: int) -> List[Dict[str, Any]]:
        """Search products using Zappos API"""
        # This is a placeholder. In a real implementation, you would call the Zappos API
        return []
    
    def _create_simulated_products(self, keywords: str, category: str, limit: int) -> List[Dict[str, Any]]:
        """
        Create simulated product data based on keywords and category
        This is a fallback method when APIs or scraping aren't available
        """
        products = []
        
        # Standardize category
        category_key = self._normalize_category(category)
        
        # Check for gender specificity
        is_womens = "women" in keywords.lower() or "woman" in keywords.lower() or "female" in keywords.lower()
        is_mens = "men" in keywords.lower() or "man" in keywords.lower() or "male" in keywords.lower()
        
        # Check for festival keywords
        is_festival = any(k in keywords.lower() for k in ["festival", "coachella", "burning man", "music festival", "concert"])
        
        # Choose appropriate brand list based on keywords
        brand_list = self.festival_brands.get(category_key, []) if is_festival else self.category_brands.get(category_key, [])
        if not brand_list:
            brand_list = self.category_brands.get("top", [])  # Fallback
            
        # Format keywords for generating product names
        keywords_formatted = keywords.replace("outfit", "").replace("coachella", "festival").strip()
        
        # Generate products
        for i in range(limit):
            # Select a relevant brand from the appropriate list
            brand = random.choice(brand_list)
            
            # Create product name and details based on keywords
            product_details = self._generate_product_details(
                keywords_formatted, 
                category_key, 
                is_festival, 
                is_womens, 
                is_mens,
                brand
            )
            
            # Add to products list
            products.append(product_details)
            
        return products
    
    def _normalize_category(self, category: str) -> str:
        """Convert any category string to one of our standard categories"""
        category = category.lower()
        
        if any(word in category for word in ["top", "shirt", "blouse", "tee", "tank"]):
            return "top"
        elif any(word in category for word in ["bottom", "pant", "jean", "short", "skirt"]):
            return "bottom"
        elif any(word in category for word in ["dress", "gown", "jumpsuit"]):
            return "dress"
        elif any(word in category for word in ["shoe", "footwear", "boot", "sandal", "heel", "sneaker"]):
            return "shoes"
        elif any(word in category for word in ["accessory", "accessories", "jewelry", "bag", "purse", "hat", "scarf"]):
            return "accessory"
        elif any(word in category for word in ["jacket", "coat", "blazer", "cardigan", "outerwear"]):
            return "outerwear"
        else:
            # Default to top if we can't identify the category
            return "top"
    
    def _generate_product_details(self, keywords: str, category: str, is_festival: bool, 
                                 is_womens: bool, is_mens: bool, brand: str) -> Dict[str, Any]:
        """Generate detailed product information based on search parameters"""
        
        # Set gender-specific adjectives
        if is_womens:
            adjectives = ["Women's", "Ladies'", "Female", "Feminine"]
        elif is_mens:
            adjectives = ["Men's", "Guys'", "Male", "Masculine"]
        else:
            adjectives = ["Unisex", "Modern", "Stylish", "Contemporary"]
            
        # Generate name based on category and context
        if is_festival:
            themes = ["Boho", "Festival", "Desert", "Summer", "Floral", "Fringe", "Crochet", "Tie-Dye"]
            theme = random.choice(themes)
            gender_prefix = random.choice(adjectives) + " " if random.random() > 0.5 else ""
            
            if category == "top":
                product_types = ["Crop Top", "Embroidered Blouse", "Crochet Tank", "Tie Front Top", "Halter Top"]
                product_type = random.choice(product_types)
                colors = ["White", "Black", "Ivory", "Tan", "Rust", "Terracotta", "Sage Green"]
                color = random.choice(colors)
                product_name = f"{gender_prefix}{theme} {color} {product_type}"
                
            elif category == "bottom":
                product_types = ["Denim Shorts", "High-Waisted Jeans", "Distressed Cutoffs", "Maxi Skirt", "Flared Pants"]
                product_type = random.choice(product_types)
                colors = ["Light Wash", "Medium Wash", "Dark Wash", "Black", "White"]
                color = random.choice(colors)
                product_name = f"{gender_prefix}{theme} {color} {product_type}"
                
            elif category == "dress":
                product_types = ["Maxi Dress", "Mini Dress", "Slip Dress", "Sundress", "Crochet Dress"]
                product_type = random.choice(product_types)
                colors = ["White", "Black", "Floral", "Tie-Dye", "Blush", "Terracotta"]
                color = random.choice(colors)
                product_name = f"{gender_prefix}{theme} {color} {product_type}"
                
            elif category == "shoes":
                product_types = ["Western Boots", "Ankle Boots", "Platform Sandals", "Gladiator Sandals", "Combat Boots"]
                product_type = random.choice(product_types)
                colors = ["Brown", "Black", "Tan", "White", "Silver"]
                color = random.choice(colors)
                product_name = f"{gender_prefix}{theme} {color} {product_type}"
                
            elif category == "accessory":
                product_types = ["Wide Brim Hat", "Statement Necklace", "Layered Necklace", "Round Sunglasses", "Fringe Bag"]
                product_type = random.choice(product_types)
                colors = ["Brown", "Black", "Tan", "Gold", "Silver", "Turquoise"]
                color = random.choice(colors)
                product_name = f"{gender_prefix}{theme} {color} {product_type}"
                
            elif category == "outerwear":
                product_types = ["Denim Jacket", "Fringe Kimono", "Embroidered Jacket", "Leather Jacket"]
                product_type = random.choice(product_types)
                colors = ["Blue", "Black", "Brown", "Ivory", "Embroidered"]
                color = random.choice(colors)
                product_name = f"{gender_prefix}{theme} {color} {product_type}"
                
            else:
                product_name = f"{gender_prefix}{theme} Festival {category.title()}"
        else:
            # Regular (non-festival) product name generation
            colors = ["Black", "White", "Blue", "Red", "Green", "Beige", "Brown", "Grey", "Navy", "Pink", "Purple"]
            color = random.choice(colors)
            gender_prefix = random.choice(adjectives) + " " if random.random() > 0.5 else ""
            
            if keywords:
                product_name = f"{gender_prefix}{color} {keywords.title()} {category.title()}"
            else:
                product_name = f"{gender_prefix}{color} {category.title()}"
        
        # Generate price based on brand and category
        designer_brands = ["PAIGE", "Re/Done", "Gianvito Rossi", "Stuart Weitzman", "Jimmy Choo", 
                          "Mansur Gavriel", "Loewe", "Citizens of Humanity", "AGOLDE"]
        
        is_designer = brand in designer_brands
        
        price_ranges = {
            "top": (50, 120) if is_designer else (25, 75),
            "bottom": (120, 250) if is_designer else (40, 120),
            "dress": (150, 350) if is_designer else (50, 180),
            "shoes": (200, 650) if is_designer else (60, 200),
            "accessory": (100, 350) if is_designer else (15, 100),
            "outerwear": (200, 450) if is_designer else (80, 250)
        }
        
        price_range = price_ranges.get(category, (50, 150))
        price = round(random.uniform(price_range[0], price_range[1]), 2)
        
        # Generate product ID
        product_id = f"sim_{brand.lower().replace(' ', '_')}_{random.randint(10000, 99999)}"
        
        # Generate realistic image URL
        # For real implementation, these would be actual product images
        # Here we're using placeholder service with appropriate search terms
        image_terms = []
        if is_festival:
            image_terms.append("festival")
            image_terms.append("coachella")
        
        if is_womens:
            image_terms.append("womens")
        elif is_mens:
            image_terms.append("mens")
            
        image_terms.append(category)
        image_terms.append(product_name.split()[-2] if len(product_name.split()) > 2 else product_name)
        
        # Real image URL would come from your product database
        # This is just a placeholder using a random image service
        image_url = f"https://source.unsplash.com/320x400/?{','.join(image_terms)}"
        
        # Create the product details
        product = {
            "product_id": product_id,
            "product_name": product_name,
            "brand": brand,
            "category": category,
            "price": price,
            "url": f"https://www.google.com/search?q={brand}+{product_name.replace(' ', '+')}",
            "image_url": image_url,
            "description": f"{product_name} from {brand} - Perfect for {keywords}"
        }
        
        return product 