import React from 'react';
import { motion } from 'framer-motion';

const OutfitCollage = ({ outfit, prompt }) => {
  if (!outfit || !outfit.items || outfit.items.length === 0) {
    return <div className="empty-state">No outfit items available</div>;
  }

  // Extract emoji from prompt if it exists
  const promptTitle = prompt || outfit.name || 'Stylish Outfit';
  const hasEmoji = /[\p{Emoji}]/u.test(promptTitle);
  
  // Log outfit data to help debug
  console.log("Outfit data:", outfit);

  // Categorize items by type
  const categories = {};
  outfit.items.forEach(item => {
    const category = item.category?.toLowerCase() || 'other';
    if (!categories[category]) {
      categories[category] = [];
    }
    categories[category].push(item);
  });

  // Get unique categories for tags
  const uniqueCategories = Object.keys(categories);
  
  // Get style tags from outfit
  const styleTags = [
    outfit.style || 'Fashion',
    outfit.occasion || 'Casual',
    ...uniqueCategories
  ].filter(Boolean);

  return (
    <div className="collage-container">
      <motion.h1 
        className="collage-title"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        {promptTitle} {!hasEmoji && '✨'}
      </motion.h1>

      <div className="collage-grid">
        {outfit.items.map((item, index) => {
          // Use the real product URL from the backend API
          const productUrl = item.purchase_url || item.product_url || '';
          
          // Create enhanced search URLs if no direct URL provided
          let finalUrl = productUrl;
          
          if (!productUrl) {
            // Create precise search terms from product details
            const productName = item.product_name || item.name || '';
            const brand = item.brand || '';
            const category = item.category || '';
            
            // Create targeted search query
            const searchTerms = [brand, productName, category].filter(term => 
              term && term !== 'Fashion Brand' && term !== 'Unknown'
            );
            const searchQuery = encodeURIComponent(searchTerms.join(' ')).trim();
            
            // Enhanced retailer selection based on brand
            const brandLower = brand.toLowerCase();
            
            // Luxury brands -> Farfetch (matches competitor approach)
            if (brandLower.includes('cinq') || brandLower.includes('sept') || 
                ['gucci', 'prada', 'versace', 'balenciaga'].some(luxury => brandLower.includes(luxury))) {
              finalUrl = `https://www.farfetch.com/shopping/search/items.aspx?q=${searchQuery}&storeid=9359`;
            }
            // Contemporary/accessible brands -> Nordstrom
            else {
              finalUrl = `https://www.nordstrom.com/sr?keyword=${searchQuery}&origin=keywordsearch`;
            }
          }
          
          // Enhanced click handler
          const handleProductClick = (e) => {
            e.preventDefault();
            
            if (finalUrl) {
              // Add analytics tracking if needed
              console.log(`Clicking product: ${item.product_name || item.name} -> ${finalUrl}`);
              
              // Open in new tab (like competitor)
              window.open(finalUrl, '_blank', 'noopener,noreferrer');
            } else {
              console.warn('No URL available for product:', item);
            }
          };

          return (
            <div key={index} className="outfit-item">
              <div 
                className="product-image-container"
                onClick={handleProductClick}
                style={{ cursor: finalUrl ? 'pointer' : 'default' }}
              >
                <img
                  src={item.image_url || item.image || '/placeholder-image.jpg'}
                  alt={item.product_name || item.name || 'Product'}
                  className="product-image clickable-image"
                  style={{
                    border: finalUrl ? '2px solid transparent' : '2px solid #ddd',
                    transition: 'all 0.2s ease'
                  }}
                  onMouseEnter={(e) => {
                    if (finalUrl) {
                      e.target.style.border = '2px solid #4a56e2';
                      e.target.style.transform = 'scale(1.02)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (finalUrl) {
                      e.target.style.border = '2px solid transparent';
                      e.target.style.transform = 'scale(1)';
                    }
                  }}
                />
                
                {/* Click indicator overlay */}
                {finalUrl && (
                  <div className="click-overlay">
                    <span className="click-text">Click to Shop</span>
                  </div>
                )}
              </div>
              
              <div className="product-details">
                {item.brand && (
                  <p className="product-brand">{item.brand}</p>
                )}
                
                <h4 className="product-name">
                  {item.product_name || item.name || 'Stylish Item'}
                </h4>
                
                {item.retailer && (
                  <p className="product-retailer">Available at {item.retailer}</p>
                )}
                
                {item.price && (
                  <p className="product-price">
                    ${typeof item.price === 'number' ? item.price.toFixed(2) : item.price}
                  </p>
                )}
                
                {/* Enhanced click button like competitor */}
                {finalUrl && (
                  <button 
                    className="shop-button"
                    onClick={handleProductClick}
                  >
                    Visit Site
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <div className="outfit-description">
        <p>{outfit.description || "A stylish outfit perfect for your occasion."}</p>
        <p className="stylist-rationale">{outfit.stylist_rationale || ""}</p>
        <p className="total-price">Total Price: ${outfit.total_price?.toFixed(2) || "N/A"}</p>
      </div>
      
      {/* Use direct HTML for links to ensure they're clickable */}
      <div className="product-sources-wrapper">
        {(() => {
          // Build HTML string directly
          let sourceHtml = '';
          
          outfit.items.forEach((item, index) => {
            // Get the item details
            const category = item.category ? 
              item.category.charAt(0).toUpperCase() + item.category.slice(1) : 
              '';
            
            // Get retailer name from item
            const originalRetailerName = item.brand || '';
            
            // Create search query using original product details
            const productName = item.product_name || '';
            const searchQuery = encodeURIComponent(`${originalRetailerName} ${productName}`).trim();
            
            // Always use only Nordstrom and Farfetch (alternating)
            const nordstromUrl = `https://www.nordstrom.com/sr?keyword=${searchQuery}`;
            const farfetchUrl = `https://www.farfetch.com/search?q=${searchQuery}`;
            
            // Alternate between Nordstrom and Farfetch
            const retailerUrl = index % 2 === 0 ? nordstromUrl : farfetchUrl;
            const retailerName = index % 2 === 0 ? "Nordstrom" : "Farfetch";
            
            // Add the proper separator based on position
            const separator = index === 0 ? '' : ', ';
            
            // Add this item to the HTML string
            sourceHtml += `${separator}${category} <a href="${retailerUrl}" target="_blank" rel="noopener noreferrer" class="retailer-link">${retailerName}</a>`;
          });
          
          return (
            <div className="product-sources">
              <div dangerouslySetInnerHTML={{ __html: sourceHtml }} />
            </div>
          );
        })()}
      </div>

      <div className="style-tags">
        {styleTags.map((tag, index) => (
          <motion.div 
            key={index} 
            className="style-tag"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3, delay: 0.5 + (index * 0.1) }}
          >
            <div className="tag-icon">
              {getTagIcon(tag)}
            </div>
            <span>{tag.charAt(0).toUpperCase() + tag.slice(1)}</span>
          </motion.div>
        ))}
      </div>

      <style jsx>{`
        .collage-container {
          background-color: #f9f9f9;
          border-radius: 24px;
          padding: 2rem;
          width: 100%;
          max-width: 1200px;
          margin: 0 auto;
          box-shadow: 0 8px 30px rgba(0, 0, 0, 0.05);
        }

        .collage-title {
          font-family: 'Playfair Display', serif;
          font-size: 2.5rem;
          text-align: center;
          margin-bottom: 2rem;
          color: #1a1a1a;
          font-weight: 600;
        }

        .collage-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
          gap: 2rem;
          margin-bottom: 2rem;
        }

        .outfit-item {
          background: white;
          border-radius: 12px;
          overflow: hidden;
          box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
          transition: transform 0.3s ease, box-shadow 0.3s ease;
          height: 100%;
          display: flex;
          flex-direction: column;
        }

        .outfit-item:hover {
          transform: translateY(-5px);
          box-shadow: 0 12px 25px rgba(0, 0, 0, 0.15);
        }

        .product-image-container {
          position: relative;
          height: 300px;
          overflow: hidden;
          border-radius: 8px;
          cursor: pointer;
        }

        .product-image {
          width: 100%;
          height: 100%;
          object-fit: cover;
          transition: all 0.3s ease;
        }

        .product-image:hover {
          transform: scale(1.05);
        }

        .clickable-image {
          cursor: pointer;
        }

        .click-overlay {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          background: rgba(0, 0, 0, 0.6);
          display: flex;
          align-items: center;
          justify-content: center;
          opacity: 0;
          transition: opacity 0.3s ease;
          border-radius: 8px;
        }

        .product-image-container:hover .click-overlay {
          opacity: 1;
        }

        .click-text {
          color: white;
          font-size: 1.2rem;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 1px;
          text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
        }

        .product-details {
          padding: 20px;
          text-align: center;
        }

        .product-brand {
          color: #666;
          margin: 0 0 8px;
          font-size: 0.9rem;
          font-weight: 500;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .product-name {
          margin: 0 0 8px;
          font-size: 1.1rem;
          font-weight: 600;
          color: #2d3748;
          line-height: 1.4;
        }

        .product-retailer {
          color: #4a56e2;
          margin: 0 0 8px;
          font-size: 0.85rem;
          font-weight: 500;
        }

        .product-price {
          font-weight: 700;
          font-size: 1.3rem;
          margin: 0 0 15px;
          color: #e53e3e;
        }

        .shop-button {
          background: linear-gradient(45deg, #4a56e2, #667eea);
          color: white;
          border: none;
          padding: 12px 24px;
          border-radius: 8px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.3s ease;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          font-size: 0.9rem;
          width: 100%;
          margin-top: 10px;
        }

        .shop-button:hover {
          background: linear-gradient(45deg, #3a46d2, #5570da);
          transform: translateY(-2px);
          box-shadow: 0 8px 20px rgba(74, 86, 226, 0.4);
        }

        .shop-button:active {
          transform: translateY(0);
          box-shadow: 0 4px 12px rgba(74, 86, 226, 0.3);
        }

        .outfit-description {
          text-align: center;
          margin-top: 2rem;
          font-size: 1.1rem;
          color: #444;
          line-height: 1.6;
        }

        .stylist-rationale {
          font-style: italic;
          color: #666;
          margin-top: 1rem;
        }

        .total-price {
          font-weight: 600;
          margin-top: 1rem;
          color: #333;
        }

        .style-tags {
          display: flex;
          flex-wrap: wrap;
          justify-content: center;
          gap: 1rem;
          margin-top: 2rem;
        }

        .style-tag {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 0.5rem;
          padding: 0.5rem;
          min-width: 80px;
        }

        .tag-icon {
          background-color: white;
          width: 50px;
          height: 50px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 1.5rem;
          box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
        }

        .style-tag span {
          font-size: 0.8rem;
          font-weight: 500;
          color: #555;
        }

        @media (min-width: 768px) {
          .collage-grid {
            grid-template-columns: repeat(3, 1fr);
          }
        }

        @media (max-width: 767px) {
          .collage-grid {
            grid-template-columns: repeat(2, 1fr);
          }
        }

        @media (max-width: 480px) {
          .collage-grid {
            grid-template-columns: 1fr;
          }
        }

        .product-sources-wrapper {
          margin: 1.5rem 0;
        }
        
        .product-sources {
          text-align: center;
          line-height: 1.8;
          color: #333;
          font-size: 1rem;
          padding: 0 1rem;
          font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        
        .retailer-link {
          color: #0066cc;
          text-decoration: underline;
          cursor: pointer;
        }
        
        .retailer-link:hover {
          color: #0044aa;
          background-color: rgba(0,0,0,0.05);
        }
      `}</style>
    </div>
  );
};

// Helper function to get appropriate icon for category/style tags
const getTagIcon = (tag) => {
  const tagMap = {
    'festival': '🎭',
    'boho': '🌿',
    'trendy': '🔥',
    'casual': '👕',
    'chic': '👗',
    'summer': '☀️',
    'winter': '❄️',
    'spring': '🌷',
    'fall': '🍂',
    'accessories': '👜',
    'shoes': '👠',
    'tops': '👚',
    'bottoms': '👖',
    'dresses': '👗',
    'outerwear': '🧥',
    'formal': '🥂',
    'coachella': '🎵',
    'beach': '🏖️',
    'office': '💼',
    'workout': '🏋️',
    'party': '🎉',
    'vintage': '📻',
    'streetwear': '🛹',
    'minimalist': '✨',
    'luxury': '💎',
    'fashion': '👒'
  };

  const lowercaseTag = tag.toLowerCase();
  return tagMap[lowercaseTag] || '✨';
};

export default OutfitCollage; 