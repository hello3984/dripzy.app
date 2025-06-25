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
 * Get the best retail URL for a product based on brand or preference
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
  
  // Default behavior - alternate between retailers
  // Use Farfetch for luxury/designer brands, Nordstrom for the rest
  const luxuryBrands = [
    'gucci', 'prada', 'balenciaga', 'valentino', 'saint laurent', 
    'fendi', 'burberry', 'off-white', 'versace', 'balmain',
    'givenchy', 'dolce', 'gabbana', 'alexander mcqueen', 'bottega veneta'
  ];
  
  const brand = (product.brand || '').toLowerCase();
  const isLuxuryBrand = luxuryBrands.some(luxuryBrand => brand.includes(luxuryBrand));
  
  return isLuxuryBrand ? getFarfetchUrl(product) : getNordstromUrl(product);
}; 