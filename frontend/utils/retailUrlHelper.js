/**
 * Retail URL Helper
 * Utilities for handling retail product URLs and search queries
 */

/**
 * Clean a product search query by removing common unnecessary terms
 * @param {string} brand - Product brand
 * @param {string} name - Product name
 * @returns {string} - Cleaned search query
 */
export const cleanSearchQuery = (brand = '', name = '') => {
  // Combine brand and name, removing null or undefined values
  const combinedQuery = [brand, name]
    .filter(Boolean)
    .join(' ')
    .trim();
  
  if (!combinedQuery) return "fashion"; // Default fallback
  
  // Clean up common unwanted terms
  return combinedQuery
    .replace(/amazon\.com/gi, '')
    .replace(/seller/gi, '')
    .replace(/\s-\s/g, ' ')
    .replace(/\([^)]*\)/g, '') // Remove anything in parentheses
    .replace(/[^\w\s]/g, ' ')  // Replace non-alphanumeric with spaces
    .replace(/\s+/g, ' ')      // Replace multiple spaces with single space
    .trim();
};

/**
 * Get proper Farfetch URL for a product
 * @param {Object} product - Product info
 * @returns {string} - Valid Farfetch URL
 */
export const getFarfetchUrl = (product) => {
  // If product has a valid direct URL, use it
  if (product.url && product.url.includes('farfetch.com')) {
    return product.url;
  }
  
  // If product has an ID, use the ID-based URL
  if (product.productId) {
    return `https://www.farfetch.com/shopping/item-${product.productId}.aspx`;
  }
  
  // Create a clean search query
  const query = cleanSearchQuery(product.brand, product.product_name);
  
  // Build a search URL with the clean query
  return `https://www.farfetch.com/shopping/women/search?q=${encodeURIComponent(query)}`;
};

/**
 * Get proper Nordstrom URL for a product
 * @param {Object} product - Product info
 * @returns {string} - Valid Nordstrom URL
 */
export const getNordstromUrl = (product) => {
  // If product has a valid direct URL, use it
  if (product.url && product.url.includes('nordstrom.com')) {
    return product.url;
  }
  
  // If product has an ID, use the ID-based URL
  if (product.productId) {
    return `https://www.nordstrom.com/s/id/${product.productId}`;
  }
  
  // Create a clean search query
  const query = cleanSearchQuery(product.brand, product.product_name);
  
  // Build a search URL with the clean query
  return `https://www.nordstrom.com/sr?keyword=${encodeURIComponent(query)}`;
};

/**
 * Get the best retail URL for a product based on FARFETCH-FIRST approach
 * @param {Object} product - Product info
 * @param {string} preferredRetailer - Preferred retailer (farfetch, nordstrom)
 * @returns {string} - Valid retail URL
 */
export const getBestRetailUrl = (product, preferredRetailer = '') => {
  // Use product's direct URL if available
  if (product.url && (product.url.includes('http://') || product.url.includes('https://'))) {
    return product.url;
  }
  
  // Use the preferred retailer if specified
  if (preferredRetailer === 'farfetch') {
    return getFarfetchUrl(product);
  } else if (preferredRetailer === 'nordstrom') {
    return getNordstromUrl(product);
  }
  
  // FARFETCH-FIRST approach: Use Farfetch for almost all products
  // Only specific exceptions use Nordstrom
  const brand = (product.brand || '').toLowerCase();
  
  // Exception 1: Athletic brands
  const athleticBrands = [
    'nike', 'adidas', 'under armour', 'lululemon', 'athleta', 'reebok',
    'alo yoga', 'alo', 'outdoor voices', 'set active', 'girlfriend collective',
    'beyond yoga', 'vuori', 'fabletics', 'spiritual gangster', 'puma', 
    'new balance', 'asics', 'brooks', 'hoka', 'on running', 'on'
  ];
  const isAthletic = athleticBrands.some(brand_name => brand.includes(brand_name));
  
  // Exception 2: Ultra-budget brands (Shein/Temu completely excluded)
  const ultraBudgetBrands = ['forever 21', 'h&m'];
  const excludedBrands = ['shein', 'temu'];  // These brands are completely blocked
  const isUltraBudget = ultraBudgetBrands.some(brand_name => brand.includes(brand_name));
  const isExcluded = excludedBrands.some(brand_name => brand.includes(brand_name));
  
  // Excluded brands get forced to Farfetch (but shouldn't appear anyway)
  if (isExcluded) {
    return getFarfetchUrl(product);  // Force Farfetch for excluded brands
  }
  
  // Use Nordstrom only for athletic/ultra-budget exceptions, Farfetch for everything else
  return (isAthletic || isUltraBudget) ? getNordstromUrl(product) : getFarfetchUrl(product);
}; 