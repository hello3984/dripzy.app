import React from 'react';
import { motion } from 'framer-motion';

const OutfitCollage = ({ outfit, prompt }) => {
  if (!outfit || !outfit.items || outfit.items.length === 0) {
    return <div className="empty-state">No outfit items available</div>;
  }

  // Create prompt title with emoji if needed
  const promptTitle = prompt || outfit.name || "Your Style";
  const hasEmoji = /[\u{1F600}-\u{1F64F}]|[\u{1F300}-\u{1F5FF}]|[\u{1F680}-\u{1F6FF}]|[\u{1F1E0}-\u{1F1FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]/u.test(promptTitle);
  
  // Artistic positioning configurations for different numbers of items
  const getItemPositions = (itemCount) => {
    switch(itemCount) {
      case 1:
        return [{ top: '20%', left: '35%', width: '300px', rotation: 0, zIndex: 1 }];
      case 2:
        return [
          { top: '15%', left: '20%', width: '280px', rotation: -5, zIndex: 2 },
          { top: '35%', left: '55%', width: '260px', rotation: 8, zIndex: 1 }
        ];
      case 3:
        return [
          { top: '10%', left: '15%', width: '250px', rotation: -8, zIndex: 3 },
          { top: '25%', left: '45%', width: '280px', rotation: 2, zIndex: 2 },
          { top: '45%', left: '25%', width: '240px', rotation: 12, zIndex: 1 }
        ];
      case 4:
        return [
          { top: '8%', left: '10%', width: '220px', rotation: -12, zIndex: 4 },
          { top: '20%', left: '40%', width: '260px', rotation: 5, zIndex: 3 },
          { top: '40%', left: '15%', width: '240px', rotation: -3, zIndex: 2 },
          { top: '35%', left: '65%', width: '200px', rotation: 15, zIndex: 1 }
        ];
      default:
        // For 5+ items, create dynamic positions
        return outfit.items.map((_, index) => ({
          top: `${10 + (index * 15) % 60}%`,
          left: `${5 + (index * 20) % 70}%`,
          width: `${200 + (index % 3) * 40}px`,
          rotation: (index % 2 === 0 ? -1 : 1) * (5 + (index % 3) * 5),
          zIndex: itemCount - index
        }));
    }
  };

  const positions = getItemPositions(outfit.items.length);

  return (
    <div className="artistic-collage-container">
      <motion.h1 
        className="collage-title"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        {promptTitle} {!hasEmoji && '✨'}
      </motion.h1>

      <div className="collage-canvas">
        {outfit.items.map((item, index) => {
          // 🔧 FIX: Always use the backend URL first (correct Amazon/Farfetch/Nordstrom URLs)
          let finalUrl = item.url || item.purchase_url || item.product_url || '';
          
          // Only create fallback URLs if backend didn't provide one
          if (!finalUrl) {
            const productName = item.product_name || item.name || '';
            const brand = item.brand || '';
            const category = item.category || '';
            
            // Clean the brand name - remove Amazon seller prefixes
            const cleanBrand = brand.replace(/^amazon\.com\s*-\s*seller\s*/i, '').trim();
            
            // Create clean search terms
            const searchTerms = [cleanBrand, productName, category].filter(term => 
              term && term !== 'Fashion Brand' && term !== 'Unknown' && term !== 'API Unavailable'
            );
            const searchQuery = encodeURIComponent(searchTerms.join(' ')).trim();
            
            // Simple fallback logic - use Farfetch as default
            finalUrl = `https://www.farfetch.com/shopping/search/items.aspx?q=${searchQuery}&storeid=9359`;
          }

          // Enhanced click handler
          const handleProductClick = (e) => {
            e.preventDefault();
            
            if (finalUrl) {
              // Open in new tab
              window.open(finalUrl, '_blank', 'noopener,noreferrer');
            }
          };

          const position = positions[index] || positions[0];

          return (
            <motion.div 
              key={index} 
              className="artistic-item"
              style={{
                position: 'absolute',
                top: position.top,
                left: position.left,
                width: position.width,
                transform: `rotate(${position.rotation}deg)`,
                zIndex: position.zIndex
              }}
              initial={{ opacity: 0, scale: 0.8, rotate: position.rotation - 10 }}
              animate={{ opacity: 1, scale: 1, rotate: position.rotation }}
              transition={{ 
                duration: 0.6, 
                delay: index * 0.2,
                type: "spring",
                stiffness: 100
              }}
              whileHover={{ 
                scale: 1.05, 
                zIndex: 999,
                transition: { duration: 0.2 }
              }}
            >
              <div 
                className="artistic-card"
                onClick={handleProductClick}
                style={{ cursor: finalUrl ? 'pointer' : 'default' }}
              >
                <div className="image-frame">
                  <img
                    src={item.image_url || item.image || '/placeholder-image.jpg'}
                    alt={item.product_name || item.name || 'Product'}
                    className="artistic-image"
                  />
                  
                  {/* Polaroid-style info strip */}
                  <div className="info-strip">
                    <div className="item-info">
                      {item.brand && (
                        <p className="mini-brand">{item.brand}</p>
                      )}
                      <p className="mini-name">
                        {(item.product_name || item.name || 'Stylish Item').substring(0, 30)}
                        {(item.product_name || item.name || '').length > 30 ? '...' : ''}
                      </p>
                      {item.price && (
                        <p className="mini-price">
                          ${typeof item.price === 'number' ? item.price.toFixed(2) : item.price}
                        </p>
                      )}
                    </div>
                  </div>
                  
                  {/* Click indicator overlay */}
                  {finalUrl && (
                    <div className="hover-overlay">
                      <div className="shop-icon">🛍️</div>
                      <span className="shop-text">Shop Now</span>
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Outfit description at bottom */}
      <motion.div 
        className="outfit-summary"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 1 }}
      >
        <p className="description-text">{outfit.description || "A stylish outfit perfect for your occasion."}</p>
        {outfit.stylist_rationale && (
          <p className="rationale-text">{outfit.stylist_rationale}</p>
        )}
        <div className="price-section">
          <span className="total-label">Complete Look:</span>
          <span className="total-amount">${outfit.total_price?.toFixed(2) || "N/A"}</span>
        </div>
      </motion.div>

      {/* Navigation dots indicator */}
      <div className="nav-dots">
        {outfit.items.map((_, index) => (
          <div key={index} className="nav-dot" />
        ))}
      </div>

      <style jsx>{`
        .artistic-collage-container {
          background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
          border-radius: 24px;
          padding: 2rem;
          width: 100%;
          max-width: 1200px;
          margin: 0 auto;
          box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
          position: relative;
          overflow: hidden;
        }

        .collage-title {
          font-family: 'Playfair Display', serif;
          font-size: 2.8rem;
          text-align: center;
          margin-bottom: 2rem;
          color: #2d3748;
          font-weight: 700;
          text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        .collage-canvas {
          position: relative;
          width: 100%;
          height: 600px;
          margin: 2rem 0;
        }

        .artistic-item {
          cursor: pointer;
        }

        .artistic-card {
          width: 100%;
          height: auto;
          transition: all 0.3s ease;
        }

        .image-frame {
          background: white;
          border-radius: 12px;
          padding: 12px;
          box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
          position: relative;
          overflow: hidden;
          border: 3px solid white;
        }

        .artistic-image {
          width: 100%;
          height: 250px;
          object-fit: cover;
          border-radius: 8px;
          transition: all 0.3s ease;
        }

        .info-strip {
          background: white;
          padding: 12px;
          margin-top: 8px;
          border-radius: 6px;
          border-top: 1px solid #e2e8f0;
        }

        .item-info {
          text-align: center;
        }

        .mini-brand {
          font-size: 0.75rem;
          color: #718096;
          margin: 0 0 4px;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .mini-name {
          font-size: 0.85rem;
          color: #2d3748;
          margin: 0 0 4px;
          font-weight: 600;
          line-height: 1.2;
        }

        .mini-price {
          font-size: 0.9rem;
          color: #e53e3e;
          margin: 0;
          font-weight: 700;
        }

        .hover-overlay {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.7);
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          opacity: 0;
          transition: opacity 0.3s ease;
          border-radius: 12px;
        }

        .artistic-card:hover .hover-overlay {
          opacity: 1;
        }

        .shop-icon {
          font-size: 2rem;
          margin-bottom: 0.5rem;
        }

        .shop-text {
          color: white;
          font-size: 1rem;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 1px;
        }

        .outfit-summary {
          background: rgba(255, 255, 255, 0.9);
          border-radius: 16px;
          padding: 2rem;
          text-align: center;
          margin-top: 2rem;
          backdrop-filter: blur(10px);
          border: 1px solid rgba(255, 255, 255, 0.2);
        }

        .description-text {
          font-size: 1.1rem;
          color: #4a5568;
          margin: 0 0 1rem;
          line-height: 1.6;
        }

        .rationale-text {
          font-style: italic;
          color: #718096;
          margin: 0 0 1.5rem;
          font-size: 0.95rem;
        }

        .price-section {
          display: flex;
          justify-content: center;
          align-items: center;
          gap: 1rem;
        }

        .total-label {
          font-size: 1.1rem;
          color: #2d3748;
          font-weight: 500;
        }

        .total-amount {
          font-size: 1.5rem;
          color: #e53e3e;
          font-weight: 700;
        }

        .nav-dots {
          display: flex;
          justify-content: center;
          gap: 0.5rem;
          margin-top: 1.5rem;
        }

        .nav-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: #cbd5e0;
          transition: all 0.3s ease;
        }

        .nav-dot:first-child {
          background: #4a56e2;
        }

        @media (max-width: 768px) {
          .collage-canvas {
            height: 500px;
          }
          
          .collage-title {
            font-size: 2.2rem;
          }
          
          .artistic-item {
            position: relative !important;
            top: auto !important;
            left: auto !important;
            width: 280px !important;
            transform: none !important;
            margin: 1rem auto;
            display: block;
          }
          
          .collage-canvas {
            height: auto;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 1.5rem;
          }
        }

        @media (max-width: 480px) {
          .artistic-item {
            width: 250px !important;
          }
          
          .collage-title {
            font-size: 1.8rem;
          }
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
    'fashion': '✨'
  };
  
  return tagMap[tag.toLowerCase()] || '✨';
};

export default OutfitCollage; 