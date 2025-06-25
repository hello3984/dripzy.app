/**
 * Helper functions for creating outfit collages
 */

/**
 * Creates a themed collage layout based on outfit items
 * @param {Array} items - Array of outfit items with category, image_url, product_name, brand, and url
 * @returns {Array} - Items with position data for absolute positioning in the collage
 */
export const createCollageLayout = (items) => {
  if (!items || items.length === 0) return [];
  
  // Define layout templates based on number of items
  const layouts = {
    // 2 items (top, bottom)
    2: [
      { left: 200, top: 100, width: 400, height: 500, zIndex: 2 }, // Top (shirt, jacket, etc)
      { left: 600, top: 350, width: 300, height: 400, zIndex: 1 }, // Bottom (pants, skirt, etc)
    ],
    // 3 items (top, bottom, shoes)
    3: [
      { left: 200, top: 100, width: 350, height: 450, zIndex: 2 }, // Top
      { left: 550, top: 200, width: 300, height: 400, zIndex: 1 }, // Bottom
      { left: 300, top: 550, width: 250, height: 200, zIndex: 3 }, // Shoes
    ],
    // 4 items (top, bottom, shoes, accessory)
    4: [
      { left: 200, top: 100, width: 350, height: 450, zIndex: 2 }, // Top
      { left: 550, top: 200, width: 300, height: 400, zIndex: 1 }, // Bottom
      { left: 300, top: 550, width: 250, height: 200, zIndex: 3 }, // Shoes
      { left: 700, top: 350, width: 150, height: 150, zIndex: 4 }, // Accessory
    ],
    // 5 items (top, bottom, shoes, accessory 1, accessory 2)
    5: [
      { left: 200, top: 100, width: 350, height: 450, zIndex: 2 }, // Top
      { left: 550, top: 200, width: 300, height: 400, zIndex: 1 }, // Bottom
      { left: 300, top: 550, width: 250, height: 200, zIndex: 3 }, // Shoes
      { left: 700, top: 350, width: 150, height: 150, zIndex: 4 }, // Accessory 1
      { left: 100, top: 350, width: 150, height: 150, zIndex: 4 }, // Accessory 2
    ],
    // 6+ items (add more accessories or layer pieces)
    6: [
      { left: 200, top: 100, width: 350, height: 450, zIndex: 2 }, // Top
      { left: 550, top: 200, width: 300, height: 400, zIndex: 1 }, // Bottom
      { left: 300, top: 550, width: 250, height: 200, zIndex: 3 }, // Shoes
      { left: 700, top: 350, width: 150, height: 150, zIndex: 4 }, // Accessory 1
      { left: 100, top: 350, width: 150, height: 150, zIndex: 4 }, // Accessory 2
      { left: 450, top: 100, width: 200, height: 300, zIndex: 5 }, // Outerwear
    ],
  };
  
  // Special layout for dress (1 large item)
  const dressLayout = [
    { left: 350, top: 100, width: 400, height: 700, zIndex: 2 }, // Dress
  ];
  
  // Get the appropriate layout based on number of items
  let layoutTemplate = layouts[Math.min(items.length, 6)] || layouts[6];
  
  // Check if this is a dress outfit
  const hasDress = items.some(item => 
    item.category === 'Dress' || 
    item.category === 'dress' || 
    item.product_name?.toLowerCase().includes('dress')
  );
  
  if (hasDress && items.length <= 2) {
    layoutTemplate = dressLayout;
  }
  
  // Categorize items
  const categories = {
    top: items.filter(item => 
      item.category === 'Top' || 
      item.category === 'top' || 
      item.category === 'Shirt' || 
      item.category === 'shirt' ||
      item.category === 'Blouse' ||
      item.category === 'blouse'
    ),
    bottom: items.filter(item => 
      item.category === 'Bottom' || 
      item.category === 'bottom' || 
      item.category === 'Pants' || 
      item.category === 'pants' ||
      item.category === 'Skirt' ||
      item.category === 'skirt' ||
      item.category === 'Shorts' ||
      item.category === 'shorts'
    ),
    dress: items.filter(item => 
      item.category === 'Dress' || 
      item.category === 'dress'
    ),
    shoes: items.filter(item => 
      item.category === 'Shoes' || 
      item.category === 'shoes' ||
      item.category === 'Footwear' ||
      item.category === 'footwear'
    ),
    accessory: items.filter(item => 
      item.category === 'Accessory' || 
      item.category === 'accessory' ||
      item.category === 'Accessories' ||
      item.category === 'accessories' ||
      item.category === 'Jewelry' ||
      item.category === 'jewelry' ||
      item.category === 'Watch' ||
      item.category === 'watch' ||
      item.category === 'Bag' ||
      item.category === 'bag'
    ),
    outerwear: items.filter(item => 
      item.category === 'Outerwear' || 
      item.category === 'outerwear' ||
      item.category === 'Jacket' ||
      item.category === 'jacket' ||
      item.category === 'Coat' ||
      item.category === 'coat'
    ),
  };
  
  // Organize items for layout
  const organizedItems = [];
  
  // For dress outfits
  if (categories.dress.length > 0) {
    organizedItems.push(...categories.dress);
    organizedItems.push(...categories.shoes);
    organizedItems.push(...categories.accessory);
    organizedItems.push(...categories.outerwear);
  } 
  // For separates outfits
  else {
    organizedItems.push(...categories.top);
    organizedItems.push(...categories.bottom);
    organizedItems.push(...categories.shoes);
    organizedItems.push(...categories.accessory);
    organizedItems.push(...categories.outerwear);
  }
  
  // If we still don't have enough organized items, add any remaining unclassified items
  const remainingItems = items.filter(item => !organizedItems.includes(item));
  organizedItems.push(...remainingItems);
  
  // Apply layout positions to items
  return organizedItems.slice(0, layoutTemplate.length).map((item, index) => {
    return {
      ...item,
      position: layoutTemplate[index],
      imageUrl: item.image_url,
      productUrl: item.url
    };
  });
};

/**
 * Gets an appropriate background color based on outfit theme or style
 * @param {string} theme - Theme/style of the outfit
 * @returns {string} - CSS color value
 */
export const getThemeBackgroundColor = (theme) => {
  if (!theme) return 'rgb(251, 249, 245)'; // Default color
  
  const themeColors = {
    casual: 'rgb(240, 245, 251)',
    formal: 'rgb(241, 236, 245)',
    business: 'rgb(235, 235, 240)',
    date: 'rgb(251, 235, 245)',
    party: 'rgb(245, 235, 251)',
    beach: 'rgb(235, 245, 251)',
    winter: 'rgb(235, 240, 245)',
    summer: 'rgb(245, 251, 235)',
    spring: 'rgb(251, 245, 235)',
    fall: 'rgb(251, 240, 230)',
  };
  
  // Check if theme contains any of our keywords
  for (const [key, color] of Object.entries(themeColors)) {
    if (theme.toLowerCase().includes(key)) {
      return color;
    }
  }
  
  return 'rgb(251, 249, 245)'; // Default color
}; 