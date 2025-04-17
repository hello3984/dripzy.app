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
        {outfit.items.map((item, index) => (
          <motion.div 
            key={item.product_id || index}
            className={`collage-item item-${index}`}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4, delay: index * 0.1 }}
          >
            <div className="item-image-container">
              {item.image_url ? (
                <Image 
                  src={item.image_url}
                  alt={item.product_name || `Fashion item ${index + 1}`}
                  width={300}
                  height={400}
                  layout="responsive"
                  className="collage-image"
                />
              ) : (
                <div className="placeholder-image">
                  <span>{item.category?.charAt(0) || '?'}</span>
                </div>
              )}
              <div className="hover-details">
                <h3>{item.product_name || `Item ${index + 1}`}</h3>
                {item.brand && <p className="brand">{item.brand}</p>}
                {item.price && <p className="price">${parseFloat(item.price).toFixed(2)}</p>}
              </div>
            </div>
          </motion.div>
        ))}
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
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          grid-auto-rows: 300px;
          gap: 1.5rem;
          margin-bottom: 2rem;
        }

        .collage-item {
          border-radius: 12px;
          overflow: hidden;
          position: relative;
        }

        .item-image-container {
          height: 100%;
          width: 100%;
          position: relative;
          overflow: hidden;
          border-radius: 12px;
          box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
          transition: transform 0.3s ease, box-shadow 0.3s ease;
        }

        .item-image-container:hover {
          transform: scale(1.03);
          box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
        }

        .placeholder-image {
          height: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
          background: linear-gradient(45deg, #f0f0f0, #e0e0e0);
        }

        .placeholder-image span {
          font-size: 3rem;
          color: #a0aec0;
          font-weight: 600;
        }

        .hover-details {
          position: absolute;
          bottom: 0;
          left: 0;
          right: 0;
          background: linear-gradient(transparent, rgba(0, 0, 0, 0.7));
          color: white;
          padding: 1rem;
          opacity: 0;
          transition: opacity 0.3s ease;
        }

        .item-image-container:hover .hover-details {
          opacity: 1;
        }

        .hover-details h3 {
          margin: 0;
          font-size: 1rem;
          font-weight: 500;
          margin-bottom: 0.25rem;
        }

        .brand {
          margin: 0;
          font-size: 0.8rem;
          opacity: 0.9;
          margin-bottom: 0.25rem;
        }

        .price {
          margin: 0;
          font-weight: 600;
          font-size: 0.9rem;
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
            grid-template-rows: repeat(2, 300px);
          }

          .item-0 {
            grid-column: 1;
            grid-row: 1 / span 2;
          }

          .item-1 {
            grid-column: 2;
            grid-row: 1;
          }

          .item-2 {
            grid-column: 3;
            grid-row: 1;
          }

          .item-3 {
            grid-column: 2 / span 2;
            grid-row: 2;
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