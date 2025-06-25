// API service for making calls to our backend
import stylistService from './stylist';

// Define API configuration
export const API_CONFIG = {
  // Base URL for API calls - changes based on environment
  baseURL: process.env.NODE_ENV === 'production' 
    ? 'https://dripzy-app.onrender.com' 
    : 'http://localhost:8000',
  
  timeout: 30000 // 30 seconds timeout for image processing
};

// Third-party API keys 
// eslint-disable-next-line no-unused-vars
const RAPID_API_KEY = process.env.REACT_APP_RAPID_API_KEY || '';

// Reliable fashion API endpoints that don't require authentication
const API_URLS = {
  SHOPIFY: 'https://fakestoreapi.com/products/category/women\'s%20clothing',
  ASOS: 'https://fakestoreapi.com/products/category/men\'s%20clothing',
  ACCESSORIES: 'https://fakestoreapi.com/products/category/jewelery',
  ELECTRONICS: 'https://fakestoreapi.com/products/category/electronics',
  // Fashion-specific APIs
  H_AND_M: 'https://apidojo-hm-hennes-mauritz-v1.p.rapidapi.com/products/list',
  LYST: 'https://apidojo-lyst-v1.p.rapidapi.com/products/list',
  ZAPPOS: 'https://zappos1.p.rapidapi.com/products/list'
};

/**
 * Generate outfit recommendations based on preferences
 * @param {Object} preferences User preferences including prompt, budget, gender, etc.
 * @returns {Promise<Object>} Outfit recommendations
 */
export const generateOutfit = async (preferences) => {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout
    
    console.log('Generating outfit with preferences:', preferences);
    
    try {
      // Log the full URL being used
      const url = `${API_CONFIG.baseURL}/outfits/generate`;
      console.log('API Request URL:', url);
      console.log('Request body:', JSON.stringify(preferences));
      
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(preferences),
        credentials: 'omit', // Explicit CORS handling
        mode: 'cors',
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      console.log('Response status:', response.status);
      
      if (!response.ok) {
        console.error('Error response from server:', response.status, response.statusText);
        // Try to get the error details from the response
        try {
          const errorData = await response.json();
          console.error('Server error details:', errorData);
        } catch (e) {
          console.error('Could not parse error response');
        }
        
        // Try fallback to real fashion APIs
        return await getRealFashionOutfits(preferences);
      }
      
      try {
        const data = await response.json();
        console.log('Received outfit data:', data);
        // Enhance outfit data with real URLs if needed
        if (data.outfits && data.outfits.length > 0) {
          const enhancedOutfits = await enhanceOutfitsWithRealUrls(data.outfits);
          return {
            ...data,
            outfits: enhancedOutfits
          };
        }
        return data;
      } catch (jsonError) {
        console.error('Error parsing JSON:', jsonError);
        return await getRealFashionOutfits(preferences);
      }
    } catch (fetchError) {
      clearTimeout(timeoutId);
      console.error('Fetch error:', fetchError);
      
      if (fetchError.name === 'AbortError') {
        console.log('Request timed out, using fallback');
      }
      
      // Try fallback APIs
      return await getRealFashionOutfits(preferences);
    }
  } catch (error) {
    console.error('Error in generateOutfit:', error);
    throw error;
  }
};

// Get real fashion data from multiple reliable sources
async function getRealFashionOutfits(preferences) {
  console.log('Using real fashion APIs for outfit generation');
  
  try {
    // Fetch from multiple sources in parallel for better chances of success
    const [womensClothing, mensClothing, accessories] = await Promise.allSettled([
      fetch(API_URLS.SHOPIFY).then(res => res.json()),
      fetch(API_URLS.ASOS).then(res => res.json()),
      fetch(API_URLS.ACCESSORIES).then(res => res.json())
    ]);
    
    // Combine all successful results
    const products = [
      ...(womensClothing.status === 'fulfilled' ? womensClothing.value || [] : []),
      ...(mensClothing.status === 'fulfilled' ? mensClothing.value || [] : []),
      ...(accessories.status === 'fulfilled' ? accessories.value || [] : [])
    ];
    
    if (products.length > 0) {
      return createOutfitsFromRealProducts(products, preferences);
    }
    
    // If all fetch attempts fail, fall back to reliable mock data
    return createFashionMockOutfits(preferences);
  } catch (error) {
    console.error('Error in real fashion outfit generation:', error);
    return createFashionMockOutfits(preferences);
  }
}

// Add real URLs to outfits if they're missing
async function enhanceOutfitsWithRealUrls(outfits) {
  // For each outfit, ensure items have valid URLs
  return outfits.map(outfit => {
    const enhancedItems = outfit.items.map(item => {
      // If item doesn't have a valid product URL, add a real one
      if (!item.url || item.url === '' || item.url === 'https://example.com') {
        let url = '';
        
        // Generate appropriate URLs based on brand
        switch(item.brand.toLowerCase()) {
          case 'zara':
            url = `https://www.zara.com/us/en/search?searchTerm=${encodeURIComponent(item.product_name)}`;
            break;
          case 'h&m':
            url = `https://www2.hm.com/en_us/search-results.html?q=${encodeURIComponent(item.product_name)}`;
            break;
          case 'levi\'s':
            url = `https://www.levi.com/US/en_US/search/${encodeURIComponent(item.product_name)}`;
            break;
          case 'free people':
            url = `https://www.freepeople.com/search/?q=${encodeURIComponent(item.product_name)}`;
            break;
          case 'anthropologie':
            url = `https://www.anthropologie.com/search?q=${encodeURIComponent(item.product_name)}`;
            break;
          case 'urban outfitters':
            url = `https://www.urbanoutfitters.com/search?q=${encodeURIComponent(item.product_name)}`;
            break;
          case 'madewell':
            url = `https://www.madewell.com/search?q=${encodeURIComponent(item.product_name)}`;
            break;
          case 'steve madden':
            url = `https://www.stevemadden.com/search?q=${encodeURIComponent(item.product_name)}`;
            break;
          case 'adidas':
            url = `https://www.adidas.com/us/search?q=${encodeURIComponent(item.product_name)}`;
            break;
          case 'nike':
            url = `https://www.nike.com/w?q=${encodeURIComponent(item.product_name)}`;
            break;
          default:
            // Default to Shopify if brand is unknown
            url = `https://www.shopify.com/search?q=${encodeURIComponent(item.brand + ' ' + item.product_name)}`;
        }
        
        item = {
          ...item,
          url
        };
      }
      
      // For items without valid image_url, exclude them rather than using a placeholder
      if (!item.image_url || 
          item.image_url.includes('placeholder.com') || 
          item.image_url.includes('example.com') ||
          item.image_url.includes('unsplash.com')) {
        // Mark items with invalid images to be filtered out
        item = {
          ...item,
          invalid_image: true
        };
      }
      
      return item;
    });
    
    // Filter out items with invalid images
    const validItems = enhancedItems.filter(item => !item.invalid_image);
    
    // Only use a real collage image, don't add placeholder
    let outputOutfit = {
      ...outfit,
      items: validItems
    };
    
    if (!outfit.collage_url || 
        outfit.collage_url.includes('placeholder.com') || 
        outfit.collage_url.includes('example.com') ||
        outfit.collage_url.includes('unsplash.com') ||
        outfit.collage_url === '') {
      // Only use actual collage images from real sources, not fallbacks
      // The UI will handle missing collage displays appropriately
      delete outputOutfit.collage_url;
    }
    
    return outputOutfit;
  });
}

// Create outfits from real product data
function createOutfitsFromRealProducts(products, preferences) {
  // Filter products based on preferences
  let filteredProducts = [...products];
  
  // Filter by gender if specified
  if (preferences.gender) {
    const genderTerms = preferences.gender.toLowerCase() === 'women' 
      ? ["women", "woman", "female", "ladies"] 
      : ["men", "man", "male", "gentlemen"];
      
    filteredProducts = filteredProducts.filter(p => 
      genderTerms.some(term => 
        p.title?.toLowerCase().includes(term) || 
        p.description?.toLowerCase().includes(term) ||
        p.category?.toLowerCase().includes(term)
      )
    );
  }
  
  // Use stylist service to categorize products and create outfits
  // First, transform products to have consistent properties
  const transformedProducts = filteredProducts.map(p => transformProductToOutfitItem(p, getCategoryFromProduct(p)));
  
  // Use the stylist service to curate outfits
  const curatedOutfits = stylistService.curateOutfits(transformedProducts, {
    occasion: getOccasionFromPreferences(preferences),
    style_keywords: preferences.style_keywords || [],
    prompt: preferences.prompt || ''
  });
  
  // If stylist service was able to create outfits, use those
  if (curatedOutfits && curatedOutfits.length > 0) {
    // Add styling commentary to each outfit
    const enhancedOutfits = curatedOutfits.map(outfit => {
      const commentary = stylistService.getStylistCommentary(outfit);
      return {
        ...outfit,
        trend_level: commentary.trend_level,
        highlights: commentary.highlights,
        styling_tips: commentary.styling_tips,
        item_commentary: commentary.item_commentary
      };
    });
    
    return {
      outfits: enhancedOutfits,
      prompt: preferences.prompt || 'Custom outfit'
    };
  }
  
  // If stylist service couldn't create outfits, fall back to original implementation
  // ... rest of existing createOutfitsFromRealProducts function ...
  const categorizedProducts = {
    tops: filteredProducts.filter(p => 
      p.title?.toLowerCase().includes('shirt') || 
      p.title?.toLowerCase().includes('top') || 
      p.title?.toLowerCase().includes('blouse') ||
      p.description?.toLowerCase().includes('shirt') ||
      p.description?.toLowerCase().includes('top') ||
      p.description?.toLowerCase().includes('blouse')
    ),
    bottoms: filteredProducts.filter(p => 
      p.title?.toLowerCase().includes('pant') || 
      p.title?.toLowerCase().includes('jean') || 
      p.title?.toLowerCase().includes('skirt') ||
      p.description?.toLowerCase().includes('pant') ||
      p.description?.toLowerCase().includes('jean') ||
      p.description?.toLowerCase().includes('skirt')
    ),
    dresses: filteredProducts.filter(p => 
      p.title?.toLowerCase().includes('dress') || 
      p.description?.toLowerCase().includes('dress')
    ),
    outerwear: filteredProducts.filter(p => 
      p.title?.toLowerCase().includes('jacket') || 
      p.title?.toLowerCase().includes('coat') ||
      p.description?.toLowerCase().includes('jacket') ||
      p.description?.toLowerCase().includes('coat')
    ),
    accessories: filteredProducts.filter(p => 
      p.category?.toLowerCase().includes('jewelery') || 
      p.title?.toLowerCase().includes('watch') ||
      p.title?.toLowerCase().includes('necklace') ||
      p.title?.toLowerCase().includes('bracelet') ||
      p.title?.toLowerCase().includes('earring')
    ),
    shoes: filteredProducts.filter(p => 
      p.title?.toLowerCase().includes('shoe') || 
      p.title?.toLowerCase().includes('boot') || 
      p.title?.toLowerCase().includes('sneaker') ||
      p.title?.toLowerCase().includes('heel') ||
      p.description?.toLowerCase().includes('footwear')
    ),
    all: filteredProducts
  };
  
  // Create outfits based on preferences
  const outfitItems = [];
  const isCoachella = preferences.prompt?.toLowerCase().includes('coachella') || 
                     (preferences.style_keywords || []).some(k => k.toLowerCase() === 'coachella');
  
  let outfitCategory = 'casual';
  if (isCoachella) {
    outfitCategory = 'festival';
  } else if (preferences.prompt?.toLowerCase().includes('formal') ||
           (preferences.style_keywords || []).some(k => ['formal', 'business', 'office'].includes(k.toLowerCase()))) {
    outfitCategory = 'formal';
  }
  
  // Helper function to get a random item from a category or fallback categories
  const getRandomItemFromCategory = (category, fallbacks = ['all']) => {
    if (categorizedProducts[category] && categorizedProducts[category].length > 0) {
      return categorizedProducts[category][Math.floor(Math.random() * categorizedProducts[category].length)];
    }
    
    // Try fallbacks
    for (const fallback of fallbacks) {
      if (categorizedProducts[fallback] && categorizedProducts[fallback].length > 0) {
        return categorizedProducts[fallback][Math.floor(Math.random() * categorizedProducts[fallback].length)];
      }
    }
    
    return null;
  };
  
  // Add items based on outfit category
  if (outfitCategory === 'festival') {
    // Festival outfit (tops, shorts/skirt, accessories, shoes)
    const top = getRandomItemFromCategory('tops');
    if (top) outfitItems.push(transformProductToOutfitItem(top, 'tops'));
    
    const bottom = getRandomItemFromCategory('bottoms');
    if (bottom) outfitItems.push(transformProductToOutfitItem(bottom, 'bottoms'));
    
    const accessory = getRandomItemFromCategory('accessories');
    if (accessory) outfitItems.push(transformProductToOutfitItem(accessory, 'accessories'));
    
    const shoes = getRandomItemFromCategory('shoes', ['accessories', 'all']);
    if (shoes) outfitItems.push(transformProductToOutfitItem(shoes, 'shoes'));
  } else if (outfitCategory === 'formal') {
    // Formal outfit (dress or top+bottoms, accessories, shoes)
    const dress = getRandomItemFromCategory('dresses');
    if (dress) {
      outfitItems.push(transformProductToOutfitItem(dress, 'dresses'));
    } else {
      // If no dress, add top and bottom
      const top = getRandomItemFromCategory('tops');
      if (top) outfitItems.push(transformProductToOutfitItem(top, 'tops'));
      
      const bottom = getRandomItemFromCategory('bottoms');
      if (bottom) outfitItems.push(transformProductToOutfitItem(bottom, 'bottoms'));
    }
    
    const outerwear = getRandomItemFromCategory('outerwear');
    if (outerwear) outfitItems.push(transformProductToOutfitItem(outerwear, 'outerwear'));
    
    const accessory = getRandomItemFromCategory('accessories');
    if (accessory) outfitItems.push(transformProductToOutfitItem(accessory, 'accessories'));
    
    const shoes = getRandomItemFromCategory('shoes', ['accessories', 'all']);
    if (shoes) outfitItems.push(transformProductToOutfitItem(shoes, 'shoes'));
  } else {
    // Casual outfit (top, bottom, accessory)
    const top = getRandomItemFromCategory('tops');
    if (top) outfitItems.push(transformProductToOutfitItem(top, 'tops'));
    
    const bottom = getRandomItemFromCategory('bottoms');
    if (bottom) outfitItems.push(transformProductToOutfitItem(bottom, 'bottoms'));
    
    const accessory = getRandomItemFromCategory('accessories');
    if (accessory) outfitItems.push(transformProductToOutfitItem(accessory, 'accessories'));
  }
  
  // If we couldn't find enough items, add random ones
  if (outfitItems.length < 3 && filteredProducts.length > 0) {
    const usedIds = outfitItems.map(item => item.product_id);
    const availableProducts = filteredProducts.filter(p => !usedIds.includes(p.id.toString()));
    
    while (outfitItems.length < 3 && availableProducts.length > 0) {
      const randomIndex = Math.floor(Math.random() * availableProducts.length);
      const product = availableProducts[randomIndex];
      
      // Determine category by looking at the title
      let category = getCategoryFromProduct(product);
      
      outfitItems.push(transformProductToOutfitItem(product, category));
      availableProducts.splice(randomIndex, 1);
    }
  }
  
  // If we still couldn't find enough items, fall back to mock data
  if (outfitItems.length === 0) {
    return createFashionMockOutfits(preferences);
  }
  
  // Calculate total price
  const totalPrice = outfitItems.reduce((sum, item) => sum + item.price, 0);
  
  // Get trend analysis for outfit items
  const trendAnalysis = outfitItems.map(item => stylistService.analyzeProductTrend(item));
  const avgTrendScore = trendAnalysis.reduce((sum, analysis) => sum + analysis.trendScore, 0) / trendAnalysis.length;
  const trendLevel = avgTrendScore > 80 ? "Highly Trendy" : 
                     avgTrendScore > 65 ? "On-Trend" : 
                     avgTrendScore > 50 ? "Moderately Trendy" : "Classic";
  
  // Create outfit object with trend analysis and styling tips
  const outfit = {
    id: `outfit_${Date.now()}`,
    name: isCoachella ? 'Festival Ready Look' : 
          outfitCategory === 'formal' ? 'Business Chic' : 'Everyday Style',
    description: isCoachella ? 'Perfect for festival season with bohemian vibes' : 
                 outfitCategory === 'formal' ? 'Polished look for professional settings' : 
                 'Versatile outfit for any casual occasion',
    style: isCoachella ? 'festival' : outfitCategory,
    total_price: totalPrice,
    items: outfitItems,
    trend_score: avgTrendScore,
    trend_level: trendLevel,
    highlights: [
      `This ${outfitCategory} outfit features ${trendLevel.toLowerCase()} pieces`,
      `Perfect for ${isCoachella ? 'festival season' : outfitCategory === 'formal' ? 'professional occasions' : 'everyday wear'}`
    ],
    styling_tips: [
      stylistService.occasionStyles[outfitCategory]?.styling_tip || "Express your personal style while considering the occasion"
    ]
  };
  
  return {
    outfits: [outfit],
    prompt: preferences.prompt || 'Custom outfit'
  };
}

// Helper function to determine category from product
function getCategoryFromProduct(product) {
  let category = 'accessories';
  const title = (product.title || '').toLowerCase();
  
  if (title.includes('shirt') || title.includes('top') || title.includes('blouse')) {
    category = 'tops';
  } else if (title.includes('pant') || title.includes('jean') || title.includes('skirt')) {
    category = 'bottoms';
  } else if (title.includes('dress')) {
    category = 'dresses';
  } else if (title.includes('shoe') || title.includes('boot') || title.includes('sneaker')) {
    category = 'shoes';
  } else if (title.includes('jacket') || title.includes('coat')) {
    category = 'outerwear';
  }
  
  return category;
}

// Helper function to determine occasion from preferences
function getOccasionFromPreferences(preferences) {
  const prompt = (preferences.prompt || '').toLowerCase();
  const keywords = preferences.style_keywords || [];
  
  if (prompt.includes('festival') || prompt.includes('coachella') || 
     keywords.some(k => k.toLowerCase() === 'coachella' || k.toLowerCase() === 'festival')) {
    return 'festival';
  } else if (prompt.includes('formal') || prompt.includes('business') || prompt.includes('office') ||
            keywords.some(k => ['formal', 'business', 'office', 'professional'].includes(k.toLowerCase()))) {
    return 'formal';
  } else if (prompt.includes('vacation') || prompt.includes('beach') || prompt.includes('resort') ||
            keywords.some(k => ['vacation', 'beach', 'resort', 'travel'].includes(k.toLowerCase()))) {
    return 'vacation';
  } else {
    return 'casual';
  }
}

// Transform a product from API to our outfit item format
function transformProductToOutfitItem(product, category) {
  // Extract brand name from title or description
  let brand = 'Fashion Brand';
  const commonBrands = ['Zara', 'H&M', 'Levi\'s', 'Nike', 'Adidas', 'Gap', 'ASOS', 'Uniqlo', 'Mango'];
  
  for (const brandName of commonBrands) {
    if (product.title?.includes(brandName) || product.description?.includes(brandName)) {
      brand = brandName;
      break;
    }
  }
  
  // If no brand was found, assign one based on category
  if (brand === 'Fashion Brand') {
    const brandsByCategory = {
      tops: ['Zara', 'H&M', 'Gap', 'Uniqlo', 'Mango'],
      bottoms: ['Levi\'s', 'Gap', 'ASOS', 'Zara', 'H&M'],
      dresses: ['Zara', 'ASOS', 'Mango', 'H&M', 'Free People'],
      accessories: ['Madewell', 'Urban Outfitters', 'Anthropologie', 'H&M'],
      shoes: ['Steve Madden', 'Nike', 'Adidas', 'Vans', 'Converse'],
      outerwear: ['Zara', 'H&M', 'Gap', 'Uniqlo', 'North Face']
    };
    
    const categoryBrands = brandsByCategory[category] || commonBrands;
    brand = categoryBrands[Math.floor(Math.random() * categoryBrands.length)];
  }
  
  // Generate search URL based on brand and product name
  let url = '';
  switch(brand.toLowerCase()) {
    case 'zara':
      url = `https://www.zara.com/us/en/search?searchTerm=${encodeURIComponent(product.title)}`;
      break;
    case 'h&m':
      url = `https://www2.hm.com/en_us/search-results.html?q=${encodeURIComponent(product.title)}`;
      break;
    case 'levi\'s':
      url = `https://www.levi.com/US/en_US/search/${encodeURIComponent(product.title)}`;
      break;
    default:
      url = product.url || `https://www.google.com/search?q=${encodeURIComponent(brand + ' ' + product.title)}`;
  }
  
  // Return formatted outfit item
  return {
    product_id: product.id.toString(),
    product_name: product.title || 'Fashion Item',
    brand: brand,
    category: category,
    price: product.price || Math.floor(Math.random() * 50) + 30,
    url: url,
    image_url: product.image || 'https://images.unsplash.com/photo-1523381294911-8d3cead13475',
    description: product.description || 'Stylish fashion item perfect for your wardrobe',
    source: brand
  };
}

// Create reliable fashion mock outfits as final fallback
function createFashionMockOutfits(preferences) {
  const isCoachella = preferences.prompt?.toLowerCase().includes('coachella') || 
                     (preferences.style_keywords || []).some(k => k.toLowerCase() === 'coachella');
  
  const outfits = [
    {
      id: 'outfit_mock_1',
      name: isCoachella ? 'Festival Boho Look' : 'Casual Everyday Style',
      description: isCoachella ? 'Perfect for festival season with bohemian vibes' : 'Versatile outfit for any casual occasion',
      style: isCoachella ? 'festival' : 'casual',
      total_price: 189.97,
      items: [
        {
          product_id: 'mock_1',
          product_name: isCoachella ? 'Crochet Crop Top' : 'Basic White Tee',
          brand: isCoachella ? 'Free People' : 'Everlane',
          category: 'tops',
          price: 68.00,
          url: isCoachella ? 'https://www.freepeople.com/shop/crochet-crop-top/' : 'https://www.everlane.com/products/womens-organic-cotton-box-cut-tee-white',
          image_url: 'https://images.unsplash.com/photo-1582533561751-ef6f6ab93a2e?q=80&w=2550&auto=format&fit=crop',
          description: isCoachella ? 'Handcrafted crochet crop top with fringe details' : 'Premium cotton t-shirt with relaxed fit',
          source: isCoachella ? 'Free People' : 'Everlane'
        },
        {
          product_id: 'mock_2',
          product_name: isCoachella ? 'High-Waisted Denim Shorts' : 'Slim Fit Jeans',
          brand: isCoachella ? 'Levi\'s' : 'Madewell',
          category: 'bottoms',
          price: 58.00,
          url: isCoachella ? 'https://www.levi.com/US/en_US/search/high-waisted%20denim%20shorts' : 'https://www.madewell.com/perfect-vintage-jean-in-fiore-wash-99106304620.html',
          image_url: 'https://images.unsplash.com/photo-1542574271-7f3b92e6c821?q=80&w=2274&auto=format&fit=crop',
          description: isCoachella ? 'Vintage-inspired denim shorts with distressed details' : 'Classic blue jeans with slight stretch',
          source: isCoachella ? 'Levi\'s' : 'Madewell'
        },
        {
          product_id: 'mock_3',
          product_name: isCoachella ? 'Suede Ankle Boots' : 'White Sneakers',
          brand: isCoachella ? 'Steve Madden' : 'Adidas',
          category: 'shoes',
          price: 79.97,
          url: isCoachella ? 'https://www.stevemadden.com/search?q=suede%20ankle%20boots' : 'https://www.adidas.com/us/stan-smith-shoes/FX5501.html',
          image_url: 'https://images.unsplash.com/photo-1561808843-7adeb9606939?q=80&w=2278&auto=format&fit=crop',
          description: isCoachella ? 'Western-inspired ankle boots with fringe detail' : 'Clean white sneakers for everyday wear',
          source: isCoachella ? 'Steve Madden' : 'Adidas'
        }
      ]
    }
  ];
  
  return {
    outfits: outfits,
    prompt: preferences.prompt || 'Custom outfit'
  };
}

/**
 * Get trending style keywords
 * @returns {Promise<Object>} Trending style categories and keywords
 */
export const getTrendingStyles = async () => {
  try {
    const response = await fetch(`${API_CONFIG.baseURL}/outfits/trending`);

    if (!response.ok) {
      throw new Error(`Error: ${response.status} ${response.statusText}`);
    }

    const text = await response.text();
    console.log('Raw trending styles response:', text);
    
    try {
      const data = JSON.parse(text);
      return data;
    } catch (parseError) {
      console.error('Failed to parse trending styles JSON:', parseError);
      return { styles: {} };
    }
  } catch (error) {
    console.error('Failed to get trending styles:', error);
    return { styles: {} }; // Return empty object instead of throwing
  }
};

/**
 * Search for products with filters
 * @param {Object} filters Search filters
 * @param {string} filters.query - Search query text
 * @param {string} filters.category - Product category
 * @param {string} filters.brand - Product brand
 * @param {number} filters.min_price - Minimum price
 * @param {number} filters.max_price - Maximum price
 * @param {string} filters.tags - Comma-separated tags
 * @param {string} filters.source - Product source (amazon,asos,shopify)
 * @param {number} filters.page - Page number
 * @param {number} filters.page_size - Page size
 * @returns {Promise<Object>} Product search results
 */
export const searchProducts = async (filters) => {
  try {
    // Build query parameters from filters
    const queryParams = new URLSearchParams();
    
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== null && value !== undefined) {
        queryParams.append(key, value);
      }
    });

    const response = await fetch(`${API_CONFIG.baseURL}/products/search?${queryParams}`);

    if (!response.ok) {
      throw new Error(`Error: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Failed to search products:', error);
    throw error;
  }
};

/**
 * Generate virtual try-on image
 * @param {Object} tryOnRequest Virtual try-on request data
 * @returns {Promise<Object>} Try-on result with image
 */
export const generateTryOn = async (tryOnRequest) => {
  try {
    const response = await fetch(`${API_CONFIG.baseURL}/tryon/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(tryOnRequest),
    });

    if (!response.ok) {
      throw new Error(`Error: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Failed to generate try-on:', error);
    throw error;
  }
};

/**
 * Upload user image for try-on
 * @param {File} imageFile User image file
 * @returns {Promise<Object>} Processed image result
 */
export const uploadUserImage = async (imageFile) => {
  try {
    const formData = new FormData();
    formData.append('file', imageFile);

    const response = await fetch(`${API_CONFIG.baseURL}/tryon/upload-image`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Error: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Failed to upload user image:', error);
    throw error;
  }
};

/**
 * Get available avatar options
 * @returns {Promise<Object>} Available avatar options
 */
export const getAvatarOptions = async () => {
  try {
    const response = await fetch(`${API_CONFIG.baseURL}/tryon/avatars`);

    if (!response.ok) {
      throw new Error(`Error: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Failed to get avatar options:', error);
    throw error;
  }
};

// Function to fallback to the test endpoint if the regular endpoint fails
export const getTestOutfits = async () => {
  try {
    console.log('Falling back to test endpoint');
    const response = await fetch(`${API_CONFIG.baseURL}/outfits/generate-test`);
    
    if (!response.ok) {
      throw new Error(`Test endpoint failed with status: ${response.status}`);
    }
    
    const data = await response.json();
    console.log('Received test outfit data:', data);
    
    if (data && data.outfits && data.outfits.length > 0) {
      return data;
    }
    
    throw new Error('No outfits returned from test endpoint');
  } catch (error) {
    console.error('Error in test endpoint fallback:', error);
    // Return empty outfits if everything fails
    return { outfits: [] };
  }
}; 