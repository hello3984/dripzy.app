from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import httpx
import os
import json
import random
from datetime import datetime

from app.services.product_service import ProductService

router = APIRouter(
    prefix="/products",
    tags=["products"],
    responses={404: {"description": "Not found"}},
)

# Models
class Product(BaseModel):
    id: str
    name: str
    brand: str
    category: str
    price: float
    url: Optional[str] = None
    image_url: str
    description: Optional[str] = None
    source: Optional[str] = "api"

class ProductSearchResult(BaseModel):
    products: List[Product]
    total: int
    page: int
    page_size: int
    
# Function to get real products from external API
async def get_real_products(
    query: Optional[str] = None,
    category: Optional[str] = None,
    brand: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    page: int = 1,
    page_size: int = 20
):
    """Get real products from external fashion API"""
    try:
        # Throttle API requests by adding a cache
        current_time = datetime.now().strftime("%Y%m%d%H")
        cache_key = f"{query}_{category}_{brand}_{min_price}_{max_price}_{page}_{current_time}"
        
        # Check if we have cached data for this request
        cached_file = f"app/cache/products_{cache_key}.json"
        os.makedirs("app/cache", exist_ok=True)
        
        if os.path.exists(cached_file):
            with open(cached_file, "r") as f:
                return json.load(f)

        # Try multiple fashion APIs in sequence until one works
        all_products = []
        
        # 1. First try ShopStyle Collective API (recommended for production)
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Convert our category to ShopStyle's categories
                shopstyle_category = ""
                if category:
                    category_mapping = {
                        "tops": "womens-tops",
                        "bottoms": "womens-jeans",
                        "dresses": "womens-dresses",
                        "shoes": "womens-shoes",
                        "accessories": "womens-accessories",
                        "outerwear": "womens-outerwear",
                        "jewelry": "womens-jewelry",
                    }
                    shopstyle_category = category_mapping.get(category.lower(), "")
                
                search_term = query if query else category if category else "fashion"
                if "coachella" in (search_term or "").lower() or "festival" in (search_term or "").lower():
                    search_term = "festival fashion"
                
                # ShopStyle API endpoint
                response = await client.get(
                    "https://api.shopstyle.com/api/v2/products",
                    params={
                        "pid": os.getenv("SHOPSTYLE_API_KEY", "uid1234567890"), # Replace with real API key
                        "limit": page_size,
                        "offset": (page - 1) * page_size,
                        "fts": search_term,
                        "cat": shopstyle_category,
                        "min": min_price,
                        "max": max_price,
                        "brand": brand
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Transform API response to our Product format
                    if "products" in data:
                        for item in data["products"]:
                            product = {
                                "id": str(item.get("id")),
                                "name": item.get("name", "Fashion Item"),
                                "brand": item.get("brand", {}).get("name", "ShopStyle"),
                                "category": category or item.get("categories", [{}])[0].get("name", "fashion") if item.get("categories") else "fashion",
                                "price": item.get("price"),
                                "url": item.get("clickUrl", ""),
                                "image_url": item.get("image", {}).get("sizes", {}).get("Best", {}).get("url", ""),
                                "description": item.get("description", "Stylish fashion item"),
                                "source": "ShopStyle"
                            }
                            all_products.append(product)
        except Exception as shopstyle_error:
            print(f"Error fetching from ShopStyle API: {str(shopstyle_error)}")
            # Continue to fallback sources
        
        # 2. Try H&M API via RapidAPI if ShopStyle fails
        if not all_products:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    # Prepare search parameters
                    search_term = query if query else category if category else "fashion"
                    
                    # Make request to H&M API via RapidAPI
                    response = await client.get(
                        "https://apidojo-hm-hennes-mauritz-v1.p.rapidapi.com/products/list",
                        headers={
                            "X-RapidAPI-Key": os.getenv("RAPID_API_KEY", ""),
                            "X-RapidAPI-Host": "apidojo-hm-hennes-mauritz-v1.p.rapidapi.com"
                        },
                        params={
                            "country": "us",
                            "lang": "en",
                            "currentpage": str(page),
                            "pagesize": str(page_size),
                            "categories": category or "",
                            "q": search_term
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Transform API response to our Product format
                        if "results" in data:
                            for item in data["results"]:
                                product = {
                                    "id": str(item.get("code", "")),
                                    "name": item.get("name", "Fashion Item"),
                                    "brand": "H&M",
                                    "category": category or item.get("categoryName", "fashion"),
                                    "price": item.get("price", {}).get("value", 0),
                                    "url": item.get("linkPdp", ""),
                                    "image_url": item.get("images", [{}])[0].get("url", "") if item.get("images") else "",
                                    "description": item.get("description", "Stylish fashion item"),
                                    "source": "H&M API"
                                }
                                all_products.append(product)
            except Exception as hm_error:
                print(f"Error fetching from H&M API: {str(hm_error)}")
                # Continue to next fallback
        
        # 3. Try ASOS API via RapidAPI if previous sources fail
        if not all_products:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    # Prepare search parameters
                    search_term = query if query else category if category else "fashion"
                    
                    # Make request to ASOS API via RapidAPI
                    response = await client.get(
                        "https://asos2.p.rapidapi.com/products/v2/list",
                        headers={
                            "X-RapidAPI-Key": os.getenv("RAPID_API_KEY", ""),
                            "X-RapidAPI-Host": "asos2.p.rapidapi.com"
                        },
                        params={
                            "store": "US",
                            "offset": (page - 1) * page_size,
                            "limit": page_size,
                            "q": search_term,
                            "sort": "freshness",
                            "currency": "USD"
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Transform API response to our Product format
                        if "products" in data:
                            for item in data["products"]:
                                product = {
                                    "id": str(item.get("id", "")),
                                    "name": item.get("name", "Fashion Item"),
                                    "brand": item.get("brandName", "ASOS"),
                                    "category": category or "fashion",
                                    "price": item.get("price", {}).get("current", {}).get("value", 0),
                                    "url": f"https://www.asos.com/us/{item.get('url', '')}" if item.get("url") else "",
                                    "image_url": f"https://{item.get('imageUrl', '')}" if item.get("imageUrl") else "",
                                    "description": "Stylish fashion item from ASOS",
                                    "source": "ASOS API"
                                }
                                all_products.append(product)
            except Exception as asos_error:
                print(f"Error fetching from ASOS API: {str(asos_error)}")
                # Continue to next fallback
        
        # 4. Try free products API if all else fails
        if not all_products:
            try:
                search_term = query if query else category if category else "fashion"
                fashion_endpoint = "products/category/clothing"
                if "jewelery" in search_term.lower() or "accessories" in search_term.lower():
                    fashion_endpoint = "products/category/jewelery"
                
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(
                        f"https://fakestoreapi.com/{fashion_endpoint}"
                    )
                    
                    if response.status_code == 200:
                        items = response.json()
                        
                        # Transform free API response to our Product format
                        for item in items:
                            # Generate realistic price based on category
                            price_range = (30, 120)
                            if category == "shoes":
                                price_range = (60, 150)
                            elif category == "accessories":
                                price_range = (20, 80)
                            elif category == "outerwear":
                                price_range = (80, 200)
                            
                            # Pick a brand from our fashion brand list
                            fashion_brands = ["Zara", "H&M", "Uniqlo", "Mango", "Forever 21", 
                                             "Urban Outfitters", "Free People", "Anthropologie", 
                                             "Asos", "Everlane", "Madewell", "Gap"]
                                
                            product = {
                                "id": f"fakestore_{item.get('id', '')}",
                                "name": item.get("title", "Fashion Item"),
                                "brand": random.choice(fashion_brands),
                                "category": category or "fashion",
                                "price": item.get("price", round(random.uniform(*price_range), 2)),
                                "url": "",
                                "image_url": item.get("image", ""),
                                "description": item.get("description", "Stylish fashion item"),
                                "source": "FakeStore API"
                            }
                            all_products.append(product)
            except Exception as fakestore_error:
                print(f"Error fetching from FakeStore API: {str(fakestore_error)}")
                # Fall back to mock data
        
        # If we have products from any real API source, cache and return them
        if all_products:
            with open(cached_file, "w") as f:
                json.dump(all_products, f)
            return all_products
        
        # If all APIs fail, fall back to our enhanced mock data
        return get_mock_products()
    
    except Exception as e:
        print(f"Error in get_real_products: {str(e)}")
        # Fall back to mock data
        return get_mock_products()

# Get mock products for fallback
def get_mock_products():
    """Get mock products for demo purposes"""
    # Core mock products with enhanced brand diversity based on budget categories
    products = [
        # Luxury Brands ($300+)
        {
            "id": "p1",
            "name": "Silk Blouse",
            "brand": "Gucci",
            "category": "tops",
            "price": 890.00,
            "url": "https://www.gucci.com/us/en/pr/women/ready-to-wear/tops-shirts/blouses/silk-blouse-p-650284ZAF8F9381",
            "image_url": "https://images.unsplash.com/photo-1559583109-3e7968136c99?q=80&w=1374&auto=format&fit=crop",
            "description": "Elegant silk blouse with signature detailing",
            "source": "mock"
        },
        {
            "id": "p2",
            "name": "Leather Shoulder Bag",
            "brand": "Saint Laurent",
            "category": "accessories",
            "price": 2350.00,
            "url": "https://www.ysl.com/en-us/shoulder-bags/le-5-a-7-hobo-bag-in-smooth-leather-6929091YQ071000.html",
            "image_url": "https://images.unsplash.com/photo-1584917865442-de89df76afd3?q=80&w=1470&auto=format&fit=crop",
            "description": "Structured leather shoulder bag with iconic YSL logo",
            "source": "mock"
        },
        {
            "id": "p3",
            "name": "Gold Statement Earrings",
            "brand": "Versace",
            "category": "jewelry",
            "price": 425.00,
            "url": "https://www.versace.com/us/en-us/women/accessories/jewelry/earrings/",
            "image_url": "https://images.unsplash.com/photo-1589128777073-53d2615c9821?q=80&w=1287&auto=format&fit=crop",
            "description": "Bold gold-tone statement earrings with Medusa motif",
            "source": "mock"
        },
        {
            "id": "p4",
            "name": "Designer Sunglasses",
            "brand": "Prada",
            "category": "accessories",
            "price": 378.00,
            "url": "https://www.prada.com/us/en/women/accessories/sunglasses.html",
            "image_url": "https://images.unsplash.com/photo-1577803645773-f96470509666?q=80&w=1470&auto=format&fit=crop",
            "description": "Geometric sunglasses with UV protection",
            "source": "mock"
        },
        
        # Premium Brands ($100-300)
        {
            "id": "p5",
            "name": "Cotton Blend Sweater",
            "brand": "AllSaints",
            "category": "tops",
            "price": 178.00,
            "url": "https://www.allsaints.com/women/sweaters/allsaints-kay-cotton-blend-sweater/",
            "image_url": "https://images.unsplash.com/photo-1576566588028-4147f3842f27?q=80&w=1064&auto=format&fit=crop",
            "description": "Relaxed-fit cotton blend sweater with textured finish",
            "source": "mock"
        },
        {
            "id": "p6",
            "name": "Slim Fit Jeans",
            "brand": "Rag & Bone",
            "category": "bottoms",
            "price": 195.00,
            "url": "https://www.ragandbone.com/collections/womens-denim",
            "image_url": "https://images.unsplash.com/photo-1541099649105-f69ad21f3246?q=80&w=1374&auto=format&fit=crop",
            "description": "Mid-rise slim fit jeans with slight stretch",
            "source": "mock"
        },
        {
            "id": "p7",
            "name": "Leather Ankle Boots",
            "brand": "Vince",
            "category": "shoes",
            "price": 295.00,
            "url": "https://www.vince.com/leather-ankle-boots",
            "image_url": "https://images.unsplash.com/photo-1543163521-1bf539c55dd2?q=80&w=1480&auto=format&fit=crop",
            "description": "Minimalist leather ankle boots with stacked heel",
            "source": "mock"
        },
        {
            "id": "p8",
            "name": "Silk Midi Dress",
            "brand": "Reformation",
            "category": "dresses",
            "price": 248.00,
            "url": "https://www.thereformation.com/categories/dresses",
            "image_url": "https://images.unsplash.com/photo-1529171890772-88a536be1fda?q=80&w=1374&auto=format&fit=crop",
            "description": "Sustainable silk midi dress with side slit",
            "source": "mock"
        },
        
        # Mid-range Brands ($50-100)
        {
            "id": "p9",
            "name": "Fringe Crossbody Bag",
            "brand": "Madewell",
            "category": "accessories",
            "price": 88.00,
            "url": "https://www.madewell.com/the-sydney-crossbody-bag-LE488.html",
            "image_url": "https://images.unsplash.com/photo-1575105341889-e90a9c5a4d4c?q=80&w=1212&auto=format&fit=crop",
            "description": "Suede crossbody bag with fringe detail",
            "source": "mock"
        },
        {
            "id": "p10",
            "name": "Layered Necklace Set",
            "brand": "Banana Republic",
            "category": "jewelry",
            "price": 58.00,
            "url": "https://bananarepublic.gap.com/browse/category.do?cid=40845",
            "image_url": "https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?q=80&w=1287&auto=format&fit=crop",
            "description": "Gold-toned layered necklace set with delicate chains",
            "source": "mock"
        },
        {
            "id": "p11",
            "name": "Denim Jacket",
            "brand": "Levi's",
            "category": "outerwear",
            "price": 98.00,
            "url": "https://www.levi.com/US/en_US/clothing/women/outerwear/c/levi_clothing_women_outerwear",
            "image_url": "https://images.unsplash.com/photo-1543076447-215ad9ba6923?q=80&w=1374&auto=format&fit=crop",
            "description": "Classic denim trucker jacket with button closure",
            "source": "mock"
        },
        {
            "id": "p12",
            "name": "Printed Midi Skirt",
            "brand": "& Other Stories",
            "category": "bottoms",
            "price": 89.00,
            "url": "https://www.stories.com/en_usd/clothing/skirts.html",
            "image_url": "https://images.unsplash.com/photo-1583496661160-fb5886a0aaaa?q=80&w=1364&auto=format&fit=crop",
            "description": "Flowy midi skirt with abstract print",
            "source": "mock"
        },
        
        # Budget Brands (Under $50)
        {
            "id": "p13",
            "name": "Graphic T-shirt",
            "brand": "H&M",
            "category": "tops",
            "price": 12.99,
            "url": "https://www2.hm.com/en_us/women/products/tops.html",
            "image_url": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?q=80&w=1480&auto=format&fit=crop",
            "description": "Cotton t-shirt with printed graphic",
            "source": "mock"
        },
        {
            "id": "p14",
            "name": "Wide-leg Trousers",
            "brand": "Zara",
            "category": "bottoms",
            "price": 45.90,
            "url": "https://www.zara.com/us/en/woman-pants-l1335.html",
            "image_url": "https://images.unsplash.com/photo-1594633312681-425c7b97ccd1?q=80&w=1374&auto=format&fit=crop",
            "description": "High-waisted wide-leg trousers with belt detail",
            "source": "mock"
        },
        {
            "id": "p15",
            "name": "Canvas Sneakers",
            "brand": "Uniqlo",
            "category": "shoes",
            "price": 29.90,
            "url": "https://www.uniqlo.com/us/en/women/shoes-and-accessories",
            "image_url": "https://images.unsplash.com/photo-1549298916-b41d501d3772?q=80&w=1412&auto=format&fit=crop",
            "description": "Minimalist canvas sneakers with rubber sole",
            "source": "mock"
        },
        {
            "id": "p16",
            "name": "Casual Sundress",
            "brand": "Old Navy",
            "category": "dresses",
            "price": 34.99,
            "url": "https://oldnavy.gap.com/browse/category.do?cid=15292",
            "image_url": "https://images.unsplash.com/photo-1515372039744-b8f02a3ae446?q=80&w=1376&auto=format&fit=crop",
            "description": "Lightweight cotton sundress with adjustable straps",
            "source": "mock"
        }
    ]
    
    # Festival-themed products from various price points
    festival_products = [
        # Luxury Festival
        {
            "id": "p17",
            "name": "Embellished Festival Jacket",
            "brand": "Chloé",
            "category": "outerwear",
            "price": 2550.00,
            "url": "https://www.chloe.com/us/outerwear_cod41997982rr.html",
            "image_url": "https://images.unsplash.com/photo-1551537482-f2075a1d41f2?q=80&w=1287&auto=format&fit=crop",
            "description": "Hand-embroidered suede jacket with fringe details",
            "source": "mock"
        },
        # Premium Festival
        {
            "id": "p18",
            "name": "Beaded Body Chain",
            "brand": "Free People",
            "category": "accessories",
            "price": 128.00,
            "url": "https://www.freepeople.com/shop/delicate-chain-crossbody",
            "image_url": "https://images.unsplash.com/photo-1611085583191-a3b181a88401?q=80&w=1374&auto=format&fit=crop",
            "description": "Delicate beaded body chain for festival layering",
            "source": "mock"
        },
        # Mid-range Festival
        {
            "id": "p19",
            "name": "Fringe Kimono",
            "brand": "Urban Outfitters",
            "category": "outerwear",
            "price": 89.00,
            "url": "https://www.urbanoutfitters.com/shop/ecote-janelle-fringe-kimono",
            "image_url": "https://images.unsplash.com/photo-1604093882750-3ed498f3178b?q=80&w=1287&auto=format&fit=crop",
            "description": "Flowy kimono with fringe trim and bohemian print",
            "source": "mock"
        },
        # Budget Festival
        {
            "id": "p20",
            "name": "Festival Hat",
            "brand": "Forever 21",
            "category": "accessories",
            "price": 24.99,
            "url": "https://www.forever21.com/us/shop/catalog/category/f21/acc_hat",
            "image_url": "https://images.unsplash.com/photo-1533055640609-24b498dfd74c?q=80&w=1374&auto=format&fit=crop",
            "description": "Wide-brim festival hat with woven band detail",
            "source": "mock"
        }
    ]
    
    products.extend(festival_products)
    return products

# Routes
@router.get("/search", response_model=ProductSearchResult)
async def search_products(
    query: Optional[str] = None,
    category: Optional[str] = None,
    brand: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    source: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """Search for products with filters"""
    try:
        # Get products - try to get real products first, fall back to mock
        try:
            products = await get_real_products(query, category, brand, min_price, max_price, page, page_size)
        except:
            # Fall back to mock data if real API fails
            products = get_mock_products()
        
        # Apply filters to products
        filtered_products = products
        
        if query:
            query = query.lower()
            filtered_products = [p for p in filtered_products if 
                               query in p["name"].lower() or 
                               query in p["description"].lower() or
                               query in p["brand"].lower() or
                               query in p["category"].lower()]
        
        if category:
            filtered_products = [p for p in filtered_products if category.lower() in p["category"].lower()]
        
        if brand:
            filtered_products = [p for p in filtered_products if brand.lower() in p["brand"].lower()]
        
        if min_price is not None:
            filtered_products = [p for p in filtered_products if p["price"] >= min_price]
        
        if max_price is not None:
            filtered_products = [p for p in filtered_products if p["price"] <= max_price]
            
        if source:
            filtered_products = [p for p in filtered_products if p.get("source", "").lower() == source.lower()]
        
        # Handle pagination
        total = len(filtered_products)
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total)
        
        paginated_products = filtered_products[start_idx:end_idx]
        
        # Convert to Product models
        product_models = [Product(**product) for product in paginated_products]
        
        return ProductSearchResult(
            products=product_models,
            total=total,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search products: {str(e)}")

@router.get("/{product_id}", response_model=Product)
async def get_product(product_id: str):
    """Get product details by ID"""
    try:
        # For now, just search mock products
        all_products = get_mock_products()
        product = next((p for p in all_products if p["id"] == product_id), None)
        
        if not product:
            raise HTTPException(status_code=404, detail=f"Product with ID {product_id} not found")
        
        return Product(**product)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get product: {str(e)}")

@router.get("/recommendations", response_model=List[Product])
async def get_product_recommendations(
    product_id: str,
    limit: int = 5
):
    """Get product recommendations based on a product ID"""
    try:
        # Initialize product service
        product_service = ProductService()
        
        # For now, we'll use mock data for recommendations
        # In a real implementation, this would query product APIs
        all_products = await product_service._get_mock_products("", None, None, 100)
        
        # Find the reference product
        reference_product = next((p for p in all_products if p["id"] == product_id), None)
        
        if not reference_product:
            raise HTTPException(status_code=404, detail=f"Product with ID {product_id} not found")
        
        # Get recommendations based on tags (in a real app, this would be more sophisticated)
        recommendations = []
        ref_tags = set([tag.lower() for tag in reference_product["tags"]])
        
        for product in all_products:
            if product["id"] == product_id:
                continue  # Skip the reference product
                
            # Calculate tag similarity (simple approach)
            product_tags = set([tag.lower() for tag in product["tags"]])
            common_tags = ref_tags.intersection(product_tags)
            
            if common_tags:
                recommendations.append((product, len(common_tags)))
        
        # Sort by number of common tags (descending)
        recommendations.sort(key=lambda x: x[1], reverse=True)
        
        # Take the top N recommendations
        top_recommendations = [Product(**rec[0]) for rec in recommendations[:limit]]
        
        return top_recommendations
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")

@router.get("/categories")
async def get_product_categories():
    """Get available product categories"""
    # In a real app, these would come from a database
    categories = [
        {"id": "top", "name": "Tops", "subcategories": ["T-Shirts", "Blouses", "Shirts", "Crop Tops"]},
        {"id": "bottom", "name": "Bottoms", "subcategories": ["Jeans", "Shorts", "Skirts", "Pants"]},
        {"id": "dress", "name": "Dresses", "subcategories": ["Casual", "Formal", "Party", "Maxi"]},
        {"id": "shoes", "name": "Shoes", "subcategories": ["Sneakers", "Boots", "Sandals", "Heels"]},
        {"id": "accessory", "name": "Accessories", "subcategories": ["Jewelry", "Bags", "Hats", "Glasses"]},
        {"id": "outerwear", "name": "Outerwear", "subcategories": ["Jackets", "Coats", "Cardigans"]}
    ]
    
    return {"categories": categories} 