import React from 'react';
import { getBestRetailUrl } from '../utils/retailUrlHelper';

const ThemeCollageGrid = ({ title, items = [] }) => {
  // Handle clicking on an item - open the product URL in a new tab
  const handleItemClick = (product) => {
    // Get the best URL using our helper function
    const url = getBestRetailUrl(product);
    
    if (url) {
      // Open in new tab with security best practices
      window.open(url, '_blank', 'noopener,noreferrer');
    }
  };

  return (
    <div className="theme-collage-container">
      {title && <h1 className="collage-title">{title}</h1>}
      
      <div className="collage-grid">
        {items.map((item, index) => (
          <div key={index} className="collage-item">
            <div 
              className="item-card"
              onClick={() => handleItemClick(item)}
              role="button"
              tabIndex={0}
              style={{ cursor: 'pointer' }}
            >
              <div className="item-image-container">
                <img 
                  src={item.image_url} 
                  alt={item.product_name || "Fashion item"} 
                  className="item-image"
                  onError={(e) => {
                    e.target.onerror = null;
                    e.target.src = "https://via.placeholder.com/300x400?text=Image+Not+Found";
                  }}
                />
                <button className="favorite-btn">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
                  </svg>
                </button>
              </div>
              
              {item.product_name && (
                <div className="item-details">
                  <h3 className="item-name">{item.product_name}</h3>
                  {item.brand && <p className="item-brand">{item.brand}</p>}
                  {item.price && <p className="item-price">${parseFloat(item.price).toFixed(2)}</p>}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
      
      <style jsx>{`
        .theme-collage-container {
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
        
        .collage-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
          grid-gap: 20px;
        }
        
        .collage-item {
          position: relative;
        }
        
        .item-card {
          background-color: white;
          border-radius: 8px;
          overflow: hidden;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
          transition: transform 0.3s ease, box-shadow 0.3s ease;
          cursor: pointer;
          height: 100%;
          display: flex;
          flex-direction: column;
        }
        
        .item-card:hover {
          transform: translateY(-5px);
          box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
        }
        
        .item-image-container {
          position: relative;
          aspect-ratio: 3/4;
          background-color: #f9f9f9;
        }
        
        .item-image {
          width: 100%;
          height: 100%;
          object-fit: cover;
          object-position: center;
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
        
        .item-details {
          padding: 1rem;
          display: flex;
          flex-direction: column;
          flex-grow: 1;
        }
        
        .item-name {
          font-size: 1rem;
          font-weight: 500;
          margin: 0 0 0.5rem;
          color: #333;
        }
        
        .item-brand {
          font-size: 0.9rem;
          color: #666;
          margin: 0 0 0.5rem;
        }
        
        .item-price {
          font-size: 1.1rem;
          font-weight: 600;
          color: #111;
          margin: 0;
          margin-top: auto;
        }
        
        @media (max-width: 768px) {
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

export default ThemeCollageGrid; 