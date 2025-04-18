import React from 'react';
import { motion } from 'framer-motion';
import Image from 'next/image';

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
          // Generate product URL
          const productUrl = item.product_url || item.url || '';
          const searchQuery = encodeURIComponent(`${item.brand || ''} ${item.product_name || ''} ${item.category || ''}`).trim();
          const fallbackUrl = `https://www.google.com/search?tbm=shop&q=${searchQuery}`;
          const finalUrl = productUrl || fallbackUrl;
          
          console.log(`Item ${index} URL:`, finalUrl);
          
          return (
            <motion.div 
              key={item.product_id || index}
              className={`collage-item item-${index}`}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.4, delay: index * 0.1 }}
            >
              <div className="product-card">
                <div className="image-container">
                  {item.image_url ? (
                    <Image 
                      src={item.image_url}
                      alt={item.product_name || `Fashion item ${index + 1}`}
                      width={300}
                      height={400}
                      className="product-image"
                    />
                  ) : (
                    <div className="placeholder-image">
                      <span>{item.category?.charAt(0) || '?'}</span>
                    </div>
                  )}
                </div>
                
                <div className="product-details">
                  <h3 className="product-name">{item.product_name || `Item ${index + 1}`}</h3>
                  {item.brand && <p className="product-brand">{item.brand}</p>}
                  {item.price && <p className="product-price">${parseFloat(item.price).toFixed(2)}</p>}
                  
                  <a 
                    href={finalUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="shop-button"
                    onClick={() => console.log("Link clicked for:", item.product_name)}
                  >
                    Shop Now
                  </a>
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>

      <div className="outfit-description">
        <p>{outfit.description || "A stylish outfit perfect for your occasion."}</p>
        <p className="stylist-rationale">{outfit.stylist_rationale || ""}</p>
        <p className="total-price">Total Price: ${outfit.total_price?.toFixed(2) || "N/A"}</p>
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

        .product-card {
          background: white;
          border-radius: 12px;
          overflow: hidden;
          box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
          transition: transform 0.3s ease, box-shadow 0.3s ease;
          height: 100%;
          display: flex;
          flex-direction: column;
        }

        .product-card:hover {
          transform: translateY(-5px);
          box-shadow: 0 12px 25px rgba(0, 0, 0, 0.15);
        }

        .image-container {
          height: 300px;
          overflow: hidden;
        }

        .product-image {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }

        .placeholder-image {
          height: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
          background: linear-gradient(45deg, #f0f0f0, #e0e0e0);
          font-size: 3rem;
          color: #a0aec0;
          font-weight: 600;
        }

        .product-details {
          padding: 1.5rem;
          display: flex;
          flex-direction: column;
          flex-grow: 1;
        }

        .product-name {
          font-size: 1.2rem;
          margin: 0 0 0.5rem;
          font-weight: 500;
        }

        .product-brand {
          color: #666;
          margin: 0 0 0.5rem;
          font-size: 0.9rem;
        }

        .product-price {
          font-weight: 600;
          font-size: 1.1rem;
          margin: 0 0 1rem;
        }

        .shop-button {
          background-color: #4a56e2;
          color: white;
          padding: 0.8rem 1rem;
          border-radius: 8px;
          text-align: center;
          font-weight: 500;
          margin-top: auto;
          text-decoration: none;
          transition: background-color 0.2s ease;
          cursor: pointer;
          display: block;
        }

        .shop-button:hover {
          background-color: #3a46d2;
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