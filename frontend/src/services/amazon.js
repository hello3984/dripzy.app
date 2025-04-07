// Amazon Associates Affiliate Link Helper

/**
 * Amazon Associates tracking ID
 */
export const AMAZON_AFFILIATE_ID = 'dripzyapp-20';

/**
 * Converts a product URL to an Amazon affiliate URL
 * @param {string} url - The original product URL
 * @param {string} source - The source of the product (amazon, etc.)
 * @returns {string} - The affiliate URL if it's an Amazon product, otherwise the original URL
 */
export const getAffiliateUrl = (url, source) => {
  // Only modify Amazon URLs
  if (!url) return '#';
  
  if (source?.toLowerCase() === 'amazon' || url.includes('amazon.com')) {
    try {
      const amazonUrl = new URL(url);
      
      // Add or replace the tag parameter
      amazonUrl.searchParams.set('tag', AMAZON_AFFILIATE_ID);
      
      return amazonUrl.toString();
    } catch (error) {
      console.error('Error creating affiliate URL:', error);
      return url;
    }
  }
  
  // Return the original URL for non-Amazon products
  return url;
};

/**
 * Creates a generic Amazon search affiliate link
 * @param {string} searchTerm - The search term
 * @returns {string} - An Amazon affiliate search URL
 */
export const getAmazonSearchUrl = (searchTerm) => {
  const encodedSearch = encodeURIComponent(searchTerm || '');
  return `https://www.amazon.com/s?k=${encodedSearch}&tag=${AMAZON_AFFILIATE_ID}`;
}; 