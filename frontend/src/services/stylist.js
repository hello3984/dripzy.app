// Fashion Stylist Service - Professional styling logic for the AI Fashion Assistant

// Current trending styles for 2025
const trendingStyles = {
  colors: [
    { name: 'Digital Lavender', hex: '#d5c0fa', popularity: 0.92 },
    { name: 'Cyber Yellow', hex: '#fbea37', popularity: 0.87 },
    { name: 'Verdigris', hex: '#5a8c7b', popularity: 0.85 },
    { name: 'Sundial', hex: '#d29d53', popularity: 0.83 },
    { name: 'Midnight Navy', hex: '#1e2a3d', popularity: 0.80 }
  ],
  patterns: [
    { name: 'Psychedelic Swirls', popularity: 0.90 },
    { name: 'Digital Glitch', popularity: 0.88 },
    { name: 'Neo-Geometric', popularity: 0.86 },
    { name: 'Botanical Prints', popularity: 0.82 },
    { name: 'AI-Generated Patterns', popularity: 0.94 }
  ],
  fabrics: [
    { name: 'Sustainable Denim', popularity: 0.95 },
    { name: 'Recycled Tech Fabrics', popularity: 0.93 },
    { name: 'Bio-Based Materials', popularity: 0.91 },
    { name: 'Temperature-Regulating Textiles', popularity: 0.89 },
    { name: 'Plant-Based Leather', popularity: 0.86 }
  ],
  silhouettes: [
    { name: 'Oversized', popularity: 0.90 },
    { name: 'Mixed Proportions', popularity: 0.87 },
    { name: 'Fluid Forms', popularity: 0.85 },
    { name: 'Structured Minimalism', popularity: 0.82 },
    { name: 'Neo-Vintage', popularity: 0.88 }
  ],
  accessories: [
    { name: 'Statement Eyewear', popularity: 0.88 },
    { name: 'Tech-Infused Jewelry', popularity: 0.91 },
    { name: 'Maximalist Bags', popularity: 0.87 },
    { name: 'Sculptural Shoes', popularity: 0.89 },
    { name: 'Climate-Adaptive Accessories', popularity: 0.90 }
  ]
};

// Style occasion matching data
const occasionStyles = {
  'casual': {
    key_pieces: ['Relaxed Jeans', 'T-shirts', 'Sneakers', 'Casual Jackets'],
    avoid: ['Formal Suits', 'Evening Gowns', 'Stiletto Heels'],
    color_palette: ['Neutral', 'Earth Tones', 'Pastels'],
    styling_tip: 'Focus on comfort without sacrificing style. Layer basics with statement pieces.'
  },
  'business': {
    key_pieces: ['Tailored Blazers', 'Structured Pants', 'Button-Down Shirts', 'Loafers'],
    avoid: ['Distressed Jeans', 'Graphic Tees', 'Athletic Wear'],
    color_palette: ['Navy', 'Charcoal', 'White', 'Burgundy'],
    styling_tip: 'Invest in quality basics that fit perfectly. Add personality with subtle accessories.'
  },
  'festival': {
    key_pieces: ['Statement Tops', 'Shorts', 'Comfortable Boots', 'Crossbody Bags'],
    avoid: ['Business Attire', 'Restrictive Clothing', 'Delicate Fabrics'],
    color_palette: ['Vibrant Hues', 'Metallics', 'Earth Tones'],
    styling_tip: 'Prioritize self-expression while considering practicality for outdoor conditions.'
  },
  'formal': {
    key_pieces: ['Tailored Suits', 'Evening Dresses', 'Formal Footwear', 'Fine Jewelry'],
    avoid: ['Casual Denim', 'Sporty Elements', 'Chunky Footwear'],
    color_palette: ['Black', 'Jewel Tones', 'Metallics', 'Classic Neutrals'],
    styling_tip: 'Focus on impeccable fit and refined details. Less is more with accessories.'
  },
  'vacation': {
    key_pieces: ['Breathable Fabrics', 'Versatile Dresses', 'Sandals', 'Sun Accessories'],
    avoid: ['Heavy Fabrics', 'Complicated Layers', 'High Maintenance Pieces'],
    color_palette: ['Bright Colors', 'Tropical Prints', 'Ocean Tones'],
    styling_tip: 'Pack versatile pieces that can be mixed and matched. Prioritize comfort in heat.'
  }
};

// Body type recommendations
const bodyTypeRecommendations = {
  'rectangle': {
    highlight: 'Create definition at the waist',
    recommended: ['Belted Garments', 'Peplum Tops', 'Wrap Dresses', 'Full or A-line Skirts'],
    avoid: ['Shapeless Garments', 'Straight Shift Dresses']
  },
  'hourglass': {
    highlight: 'Emphasize the defined waist',
    recommended: ['Wrap Dresses', 'High-Waisted Bottoms', 'Fitted Tops', 'Curve-Hugging Silhouettes'],
    avoid: ['Boxy Shapes', 'Oversized Styles', 'Drop-Waist Designs']
  },
  'pear': {
    highlight: 'Balance proportions between upper and lower body',
    recommended: ['Statement Tops', 'Wide Necklines', 'A-line Skirts', 'Dark Colors for Bottom Half'],
    avoid: ['Skinny Jeans', 'Tapered Pants', 'Voluminous Skirts']
  },
  'apple': {
    highlight: 'Create definition and draw attention away from midsection',
    recommended: ['Empire Waistlines', 'V-necks', 'Straight or Flared Leg Pants', 'Structured Jackets'],
    avoid: ['Clingy Fabrics', 'Bulky Waistbands', 'Cropped Tops']
  },
  'athletic': {
    highlight: 'Add curves and softness to muscular frame',
    recommended: ['Ruffles', 'Feminine Details', 'Soft Fabrics', 'Full Skirts'],
    avoid: ['Straight Column Dresses', 'Very Structured Garments']
  }
};

// Fashion personality types
const fashionPersonalities = {
  'classic': {
    keywords: ['Timeless', 'Refined', 'Polished', 'Quality-focused'],
    icons: ['Audrey Hepburn', 'Grace Kelly', 'Meghan Markle'],
    signature_pieces: ['Tailored Blazers', 'White Button-Downs', 'Straight-Leg Trousers']
  },
  'bohemian': {
    keywords: ['Free-spirited', 'Eclectic', 'Artistic', 'Nature-inspired'],
    icons: ['Sienna Miller', 'Florence Welch', 'Stevie Nicks'],
    signature_pieces: ['Flowy Maxi Dresses', 'Fringe Details', 'Layered Jewelry']
  },
  'minimalist': {
    keywords: ['Streamlined', 'Understated', 'Functional', 'Quality-focused'],
    icons: ['Rosie Huntington-Whiteley', 'Mary-Kate & Ashley Olsen', 'Phoebe Philo'],
    signature_pieces: ['Monochromatic Looks', 'Architectural Silhouettes', 'Limited Color Palette']
  },
  'avant-garde': {
    keywords: ['Experimental', 'Boundary-pushing', 'Artistic', 'Statement-making'],
    icons: ['Lady Gaga', 'Tilda Swinton', 'Björk'],
    signature_pieces: ['Unconventional Silhouettes', 'Conceptual Pieces', 'Artistic Details']
  },
  'streetwear': {
    keywords: ['Urban', 'Bold', 'Comfort-focused', 'Trend-aware'],
    icons: ['Rihanna', 'Billie Eilish', 'Zendaya'],
    signature_pieces: ['Graphic Tees', 'Sneakers', 'Athleisure Elements']
  }
};

// Color season analysis
const colorSeasonAnalysis = {
  'spring': {
    characteristics: 'Warm and bright coloring',
    best_colors: ['Coral', 'Peach', 'Warm Yellow', 'Apple Green', 'Light Turquoise'],
    avoid_colors: ['Black', 'Dark Brown', 'Navy Blue', 'Grey']
  },
  'summer': {
    characteristics: 'Cool and soft coloring',
    best_colors: ['Soft Pink', 'Lavender', 'Powder Blue', 'Mint', 'Light Grey'],
    avoid_colors: ['Orange', 'Bright Yellow', 'Tomato Red', 'Chocolate Brown']
  },
  'autumn': {
    characteristics: 'Warm and muted coloring',
    best_colors: ['Olive Green', 'Rust', 'Terracotta', 'Mustard', 'Warm Brown'],
    avoid_colors: ['Black', 'Icy Blue', 'Fuchsia', 'Cool Pastels']
  },
  'winter': {
    characteristics: 'Cool and bright coloring',
    best_colors: ['True Red', 'Royal Blue', 'Emerald', 'Pure White', 'Black'],
    avoid_colors: ['Orange', 'Warm Brown', 'Muted Colors', 'Off-White']
  }
};

/**
 * Analyzes a product item to determine its trend and style score
 * @param {Object} product - Product item with properties like title, description, brand
 * @return {Object} Analysis results including trend score and style matches
 */
export const analyzeProductTrend = (product) => {
  let trendScore = 0;
  const matchedTrends = [];
  
  // Check for trending colors
  const productDesc = (product.description || '').toLowerCase();
  const productTitle = (product.title || product.product_name || '').toLowerCase();
  const combinedText = productDesc + ' ' + productTitle;
  
  // Check for color trends
  trendingStyles.colors.forEach(color => {
    if (combinedText.includes(color.name.toLowerCase())) {
      trendScore += color.popularity * 10;
      matchedTrends.push(`Trending color: ${color.name}`);
    }
  });
  
  // Check for pattern trends
  trendingStyles.patterns.forEach(pattern => {
    if (combinedText.includes(pattern.name.toLowerCase())) {
      trendScore += pattern.popularity * 8;
      matchedTrends.push(`Trending pattern: ${pattern.name}`);
    }
  });
  
  // Check for fabric trends
  trendingStyles.fabrics.forEach(fabric => {
    if (combinedText.includes(fabric.name.toLowerCase())) {
      trendScore += fabric.popularity * 7;
      matchedTrends.push(`Trending fabric: ${fabric.name}`);
    }
  });
  
  // Check for silhouette trends
  trendingStyles.silhouettes.forEach(silhouette => {
    if (combinedText.includes(silhouette.name.toLowerCase())) {
      trendScore += silhouette.popularity * 9;
      matchedTrends.push(`Trending silhouette: ${silhouette.name}`);
    }
  });
  
  // Check if it's a standout brand (higher quality/desirability)
  const premiumBrands = ['Zara', 'H&M', 'Madewell', 'Anthropologie', 'Free People', 'Levi\'s', 'Urban Outfitters'];
  const luxuryBrands = ['Gucci', 'Prada', 'Louis Vuitton', 'Chanel', 'Dior', 'Saint Laurent'];
  
  if (premiumBrands.some(brand => (product.brand || '').toLowerCase().includes(brand.toLowerCase()))) {
    trendScore += 15;
    matchedTrends.push(`Premium brand: ${product.brand}`);
  }
  
  if (luxuryBrands.some(brand => (product.brand || '').toLowerCase().includes(brand.toLowerCase()))) {
    trendScore += 30;
    matchedTrends.push(`Luxury brand: ${product.brand}`);
  }
  
  // Calculate final normalized score (0-100)
  const normalizedScore = Math.min(Math.round(trendScore), 100);
  
  return {
    trendScore: normalizedScore,
    matchedTrends,
    isHighTrend: normalizedScore > 70,
    isMediumTrend: normalizedScore > 40 && normalizedScore <= 70,
    isLowTrend: normalizedScore <= 40
  };
};

/**
 * Determines best match for an occasion from a set of products
 * @param {Array} products - Array of product items
 * @param {string} occasion - Type of occasion (casual, business, festival, etc)
 * @return {Array} Sorted and scored products for the occasion
 */
export const findOccasionMatches = (products, occasion) => {
  const occasionData = occasionStyles[occasion?.toLowerCase()] || occasionStyles.casual;
  
  return products.map(product => {
    let score = 0;
    const matchReasons = [];
    const productDesc = ((product.description || '') + ' ' + (product.title || product.product_name || '')).toLowerCase();
    
    // Check if product matches key pieces for this occasion
    occasionData.key_pieces.forEach(piece => {
      if (productDesc.includes(piece.toLowerCase())) {
        score += 20;
        matchReasons.push(`Key piece for ${occasion}: ${piece}`);
      }
    });
    
    // Check if product should be avoided for this occasion
    let avoidMatch = false;
    occasionData.avoid.forEach(piece => {
      if (productDesc.includes(piece.toLowerCase())) {
        score -= 15;
        avoidMatch = true;
        matchReasons.push(`Not ideal for ${occasion}: ${piece}`);
      }
    });
    
    // Check if product matches color palette for this occasion
    occasionData.color_palette.forEach(color => {
      if (productDesc.includes(color.toLowerCase())) {
        score += 10;
        matchReasons.push(`Good color for ${occasion}: ${color}`);
      }
    });
    
    // Add trend score
    const { trendScore } = analyzeProductTrend(product);
    score += trendScore / 5; // Weight trend as 20% of occasion match
    
    return {
      ...product,
      occasionScore: Math.max(0, Math.min(score, 100)), // Ensure score is between 0-100
      occasionMatch: score > 50,
      matchReasons,
      stylingTip: !avoidMatch ? occasionData.styling_tip : `Consider alternatives more suitable for ${occasion} occasions`
    };
  }).sort((a, b) => b.occasionScore - a.occasionScore);
};

/**
 * Curates outfit combinations based on styling principles and trend analysis
 * @param {Array} products - Array of product items from different categories
 * @param {Object} preferences - User preferences including occasion, style, etc
 * @return {Array} Curated outfits with styling explanations
 */
export const curateOutfits = (products, preferences = {}) => {
  const outfits = [];
  const occasion = preferences.occasion || (preferences.prompt?.includes('festival') ? 'festival' : 'casual');
  
  // Group products by category
  const productsByCategory = {
    tops: products.filter(p => p.category?.toLowerCase() === 'tops'),
    bottoms: products.filter(p => p.category?.toLowerCase() === 'bottoms'),
    dresses: products.filter(p => p.category?.toLowerCase() === 'dresses'),
    outerwear: products.filter(p => p.category?.toLowerCase() === 'outerwear'),
    shoes: products.filter(p => p.category?.toLowerCase() === 'shoes'),
    accessories: products.filter(p => p.category?.toLowerCase() === 'accessories'),
  };
  
  // Get occasion-matched products
  const occasionMatched = {
    tops: findOccasionMatches(productsByCategory.tops, occasion),
    bottoms: findOccasionMatches(productsByCategory.bottoms, occasion),
    dresses: findOccasionMatches(productsByCategory.dresses, occasion),
    outerwear: findOccasionMatches(productsByCategory.outerwear, occasion),
    shoes: findOccasionMatches(productsByCategory.shoes, occasion),
    accessories: findOccasionMatches(productsByCategory.accessories, occasion),
  };
  
  // Create outfit combinations
  // Outfit type 1: Top + Bottom + Shoes + Accessory
  if (occasionMatched.tops.length > 0 && occasionMatched.bottoms.length > 0) {
    const top = occasionMatched.tops[0];
    const bottom = occasionMatched.bottoms[0];
    const shoes = occasionMatched.shoes.length > 0 ? occasionMatched.shoes[0] : null;
    const accessory = occasionMatched.accessories.length > 0 ? occasionMatched.accessories[0] : null;
    
    const outfitItems = [top, bottom];
    if (shoes) outfitItems.push(shoes);
    if (accessory) outfitItems.push(accessory);
    
    const totalPrice = outfitItems.reduce((sum, item) => sum + (item.price || 0), 0);
    const trendScores = outfitItems.map(item => analyzeProductTrend(item).trendScore);
    const avgTrendScore = trendScores.reduce((sum, score) => sum + score, 0) / trendScores.length;
    
    outfits.push({
      id: `outfit_${Date.now()}_1`,
      name: `${avgTrendScore > 70 ? 'Trending ' : ''}${occasion.charAt(0).toUpperCase() + occasion.slice(1)} Look`,
      description: `Perfectly styled ${occasion} outfit with on-trend pieces`,
      style: occasion,
      total_price: totalPrice,
      items: outfitItems,
      trend_score: avgTrendScore,
      styling_notes: `This outfit combines a ${top.product_name} with ${bottom.product_name} for a stylish ${occasion} look.`,
      stylist_tip: occasionStyles[occasion]?.styling_tip || "Focus on comfort and personal expression"
    });
  }
  
  // Outfit type 2: Dress + Shoes + Accessory
  if (occasionMatched.dresses.length > 0) {
    const dress = occasionMatched.dresses[0];
    const shoes = occasionMatched.shoes.length > 0 ? occasionMatched.shoes[0] : null;
    const accessory = occasionMatched.accessories.length > 0 ? occasionMatched.accessories[0] : null;
    
    const outfitItems = [dress];
    if (shoes) outfitItems.push(shoes);
    if (accessory) outfitItems.push(accessory);
    
    const totalPrice = outfitItems.reduce((sum, item) => sum + (item.price || 0), 0);
    const trendScores = outfitItems.map(item => analyzeProductTrend(item).trendScore);
    const avgTrendScore = trendScores.reduce((sum, score) => sum + score, 0) / trendScores.length;
    
    outfits.push({
      id: `outfit_${Date.now()}_2`,
      name: `${avgTrendScore > 70 ? 'Statement ' : ''}${occasion.charAt(0).toUpperCase() + occasion.slice(1)} Ensemble`,
      description: `Effortlessly stylish ${occasion} outfit centered around a stunning dress`,
      style: occasion,
      total_price: totalPrice,
      items: outfitItems,
      trend_score: avgTrendScore,
      styling_notes: `This outfit features a stunning ${dress.product_name} as the centerpiece, perfectly suited for ${occasion} occasions.`,
      stylist_tip: `Let the dress be the focal point with complementary accessories that don't compete for attention.`
    });
  }
  
  // Return outfits or empty array if none could be created
  return outfits.length > 0 ? outfits : [];
};

/**
 * Provides expert stylist commentary on an outfit
 * @param {Object} outfit - Complete outfit with items
 * @return {Object} Styling commentary and tips
 */
export const getStylistCommentary = (outfit) => {
  // Get trend analysis for all items
  const itemAnalysis = outfit.items.map(item => ({
    item: item,
    analysis: analyzeProductTrend(item)
  }));
  
  // Find the most trendy item
  const mostTrendyItem = [...itemAnalysis].sort((a, b) => b.analysis.trendScore - a.analysis.trendScore)[0];
  
  // Calculate overall trend score
  const overallTrendScore = itemAnalysis.reduce((sum, item) => sum + item.analysis.trendScore, 0) / itemAnalysis.length;
  
  // Generate outfit highlights
  const highlights = [];
  if (overallTrendScore > 80) {
    highlights.push("This outfit features cutting-edge pieces aligned with current runway trends");
  } else if (overallTrendScore > 65) {
    highlights.push("This outfit incorporates several on-trend elements with timeless pieces");
  } else if (overallTrendScore > 50) {
    highlights.push("This outfit balances current trends with classic styling");
  } else {
    highlights.push("This outfit focuses on timeless appeal rather than fleeting trends");
  }
  
  // Add highlight for most trendy item if it's significantly trendy
  if (mostTrendyItem && mostTrendyItem.analysis.trendScore > 70) {
    highlights.push(`The ${mostTrendyItem.item.product_name} is a standout piece featuring ${mostTrendyItem.analysis.matchedTrends[0] || 'current trends'}`);
  }
  
  // Generate styling tips based on occasion
  const occasionTips = {};
  if (outfit.style) {
    const occasionStyle = occasionStyles[outfit.style.toLowerCase()] || occasionStyles.casual;
    occasionTips.key_pieces = occasionStyle.key_pieces;
    occasionTips.color_palette = occasionStyle.color_palette;
    occasionTips.styling_tip = occasionStyle.styling_tip;
  }
  
  return {
    trend_level: overallTrendScore > 80 ? "Highly Trendy" : 
                 overallTrendScore > 65 ? "On-Trend" : 
                 overallTrendScore > 50 ? "Moderately Trendy" : "Classic",
    highlights,
    styling_tips: [
      occasionTips.styling_tip || "Express your personal style while considering the occasion",
      `Consider ${outfit.style === 'formal' ? 'minimal' : 'statement'} accessories to complete this look`,
      `This outfit works well for ${outfit.style || 'casual'} occasions`
    ],
    item_commentary: itemAnalysis.map(analysis => ({
      item_name: analysis.item.product_name,
      trend_score: analysis.analysis.trendScore,
      key_trends: analysis.analysis.matchedTrends.slice(0, 2),
      styling_advice: analysis.analysis.trendScore > 70 
        ? "Let this trendy piece be the focal point" 
        : "Pair with trendier items to elevate the look"
    }))
  };
};

export default {
  analyzeProductTrend,
  findOccasionMatches,
  curateOutfits,
  getStylistCommentary,
  trendingStyles,
  occasionStyles,
  bodyTypeRecommendations,
  fashionPersonalities,
  colorSeasonAnalysis
}; 