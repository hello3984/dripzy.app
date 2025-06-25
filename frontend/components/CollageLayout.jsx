import React from 'react';
import { getBestRetailUrl } from '../utils/retailUrlHelper';

const CollageLayout = ({ title, items = [] }) => {
  // Handle clicking on an item - open the product URL in a new tab
  const handleItemClick = (product) => {
    // Get the best URL using our helper function
    const url = getBestRetailUrl(product);
    
    if (url) {
      window.open(url, '_blank', 'noopener,noreferrer');
    }
  };
  
  // Default background color
  const bgColor = 'rgb(251, 249, 245)';
  
  return (
    <div className="collage-container">
      {title && <h1 className="collage-title">{title}</h1>}
      
      <div className="collage-content">
        <div className="collage-view" style={{ backgroundColor: bgColor }}>
          <div className="collage-carousel">
            <div className="absolute-container">
              {/* Main item (often a dress or top) */}
              {items[0] && (
                <div 
                  className="collage-item main-item"
                  onClick={() => handleItemClick(items[0])}
                >
                  <img 
                    src={items[0].image_url} 
                    alt={items[0].product_name || "Fashion item"}
                    className="item-image"
                  />
                  <button className="favorite-btn">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
                    </svg>
                  </button>
                </div>
              )}
              
              {/* Second item (often bottoms) */}
              {items[1] && (
                <div 
                  className="collage-item secondary-item"
                  onClick={() => handleItemClick(items[1])}
                >
                  <img 
                    src={items[1].image_url} 
                    alt={items[1].product_name || "Fashion item"}
                    className="item-image"
                  />
                </div>
              )}
              
              {/* Third item (often shoes or accessory) */}
              {items[2] && (
                <div 
                  className="collage-item accessory-item-1"
                  onClick={() => handleItemClick(items[2])}
                >
                  <img 
                    src={items[2].image_url} 
                    alt={items[2].product_name || "Fashion item"}
                    className="item-image"
                  />
                </div>
              )}
              
              {/* Fourth item (often accessory) */}
              {items[3] && (
                <div 
                  className="collage-item accessory-item-2"
                  onClick={() => handleItemClick(items[3])}
                >
                  <img 
                    src={items[3].image_url} 
                    alt={items[3].product_name || "Fashion item"}
                    className="item-image"
                  />
                </div>
              )}
            </div>
          </div>
        </div>
        
        {/* Outfit details */}
        <div className="outfit-details">
          <h2 className="outfit-name">Stylish Outfit</h2>
          <div className="outfit-price">
            ${items.reduce((sum, item) => sum + (parseFloat(item.price) || 0), 0).toFixed(2)}
          </div>
          
          <p className="outfit-description">
            A perfectly curated outfit featuring premium pieces for a stylish look.
          </p>
          
          {/* Brand links */}
          <div className="outfit-brands">
            {items.map((item, index) => (
              <React.Fragment key={index}>
                {index > 0 && ', '}
                <span className="category-name">{item.category || 'Item'}</span> 
                <a 
                  href={getBestRetailUrl(item)} 
                  target="_blank" 
                  rel="noopener noreferrer"
                >
                  {item.brand || 'Brand'}
                </a>
              </React.Fragment>
            ))}
          </div>
          
          {/* Tags */}
          <div className="outfit-tags">
            <button className="tag-button">date night</button>
          </div>
        </div>
      </div>
      
      <style jsx>{`
        .collage-container {
          font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif;
          max-width: 1200px;
          margin: 0 auto;
          padding: 2rem;
        }
        
        .collage-title {
          font-size: 2rem;
          font-weight: 600;
          margin-bottom: 2rem;
          text-align: center;
          color: #333;
        }
        
        .collage-content {
          display: flex;
          flex-direction: column;
        }
        
        .collage-view {
          position: relative;
          border-radius: 1rem;
          overflow: hidden;
          height: 80vh;
          max-height: 800px;
          margin-bottom: 2rem;
        }
        
        .collage-carousel {
          width: 100%;
          height: 100%;
          position: relative;
        }
        
        .absolute-container {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
        }
        
        .collage-item {
          position: absolute;
          background-color: white;
          border-radius: 8px;
          overflow: hidden;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
          cursor: pointer;
          transition: transform 0.3s ease;
        }
        
        .collage-item:hover {
          transform: scale(1.05);
          z-index: 10;
        }
        
        .main-item {
          left: 5%;
          top: 10%;
          width: 40%;
          height: 75%;
          z-index: 2;
        }
        
        .secondary-item {
          left: 48%;
          top: 15%;
          width: 30%;
          height: 60%;
          z-index: 1;
        }
        
        .accessory-item-1 {
          left: 25%;
          top: 70%;
          width: 20%;
          height: 25%;
          z-index: 3;
        }
        
        .accessory-item-2 {
          left: 65%;
          top: 50%;
          width: 20%;
          height: 25%;
          z-index: 3;
        }
        
        .item-image {
          width: 100%;
          height: 100%;
          object-fit: contain;
          background-color: white;
        }
        
        .favorite-btn {
          position: absolute;
          top: 10px;
          right: 10px;
          width: 36px;
          height: 36px;
          border-radius: 50%;
          background-color: white;
          border: none;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          z-index: 10;
          transition: transform 0.2s ease;
        }
        
        .favorite-btn:hover {
          transform: scale(1.1);
        }
        
        .favorite-btn svg {
          width: 20px;
          height: 20px;
          color: #666;
        }
        
        .outfit-details {
          padding: 2rem;
          background-color: white;
          border-radius: 1rem;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        }
        
        .outfit-name {
          font-size: 1.8rem;
          font-weight: 600;
          margin: 0 0 0.5rem;
          color: #333;
        }
        
        .outfit-price {
          font-size: 1.5rem;
          font-weight: 700;
          color: #ff6b6b;
          margin-bottom: 1rem;
        }
        
        .outfit-description {
          font-size: 1rem;
          color: #666;
          margin-bottom: 1.5rem;
          line-height: 1.6;
        }
        
        .outfit-brands {
          display: flex;
          flex-wrap: wrap;
          gap: 0.5rem;
          margin-bottom: 1.5rem;
          color: #888;
          font-size: 1rem;
          line-height: 1.5;
        }
        
        .category-name {
          color: #555;
          font-weight: 500;
          margin-right: 0.25rem;
        }
        
        .outfit-brands a {
          color: #0066cc;
          text-decoration: underline;
          cursor: pointer;
          margin: 0 0.25rem;
        }
        
        .outfit-tags {
          display: flex;
          flex-wrap: wrap;
          gap: 0.5rem;
        }
        
        .tag-button {
          background-color: #ffd7d7;
          color: #333;
          padding: 0.5rem 1rem;
          border-radius: 2rem;
          font-size: 0.9rem;
          font-weight: 500;
          border: none;
          display: inline-flex;
          align-items: center;
          gap: 0.5rem;
          cursor: pointer;
        }
        
        @media (max-width: 768px) {
          .collage-view {
            height: 60vh;
          }
          
          .main-item {
            left: 50%;
            top: 5%;
            width: 80%;
            height: 40%;
            transform: translateX(-50%);
          }
          
          .secondary-item {
            left: 50%;
            top: 50%;
            width: 60%;
            height: 35%;
            transform: translateX(-50%);
          }
          
          .accessory-item-1, .accessory-item-2 {
            display: none;
          }
        }
      `}</style>
    </div>
  );
};

export default CollageLayout; 