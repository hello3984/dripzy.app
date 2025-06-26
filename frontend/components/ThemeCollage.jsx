import React, { useState } from 'react';
import { getBestRetailUrl } from '../utils/retailUrlHelper';

const ThemeCollage = ({ title, items = [], style }) => {
  // Layout state - toggle between 'overlapping' and 'scattered'
  const [layoutStyle, setLayoutStyle] = useState('scattered'); // Default to cleaner layout
  
  // Handle clicking on an item - open the product URL in a new tab
  const handleItemClick = (product) => {
    const url = getBestRetailUrl(product);
    if (url) {
      window.open(url, '_blank', 'noopener,noreferrer');
    }
  };

  // Extract background color from style prop
  const bgColor = style?.backgroundColor || 'rgb(251, 249, 245)';
  
  // Calculate total price if items have prices
  const totalPrice = items?.reduce((sum, item) => sum + (parseFloat(item.price) || 0), 0) || 453.80;
  
  // Get a description from the first item or use default
  const description = items?.[0]?.description || 
    "A playful and feminine look featuring a flowy floral dress, paired with delicate accessories and strappy heels for a romantic date night.";
  
  // Determine outfit name
  const outfitName = title?.replace('👑', '').trim() || "Stylish Outfit";
  
  // IMPROVED: Better positioning logic to prevent excessive overlapping
  const generateBetterPositions = (items) => {
    if (!items || items.length === 0) return [];
    
    const containerWidth = 800;
    const containerHeight = 600;
    
    if (layoutStyle === 'scattered') {
      // Gensmo-style clean scattered layout
      return items.map((item, index) => {
        const scatteredPositions = [
          { left: 80, top: 60, width: 180, height: 220 },
          { left: 320, top: 120, width: 160, height: 200 },
          { left: 550, top: 90, width: 170, height: 210 },
          { left: 150, top: 320, width: 165, height: 195 },
          { left: 420, top: 350, width: 175, height: 215 },
          { left: 90, top: 480, width: 160, height: 190 }
        ];
        
        const position = scatteredPositions[index] || {
          left: (index % 3) * (containerWidth / 3) + 40,
          top: Math.floor(index / 3) * (containerHeight / 2) + 40,
          width: 170,
          height: 200
        };
        
        return {
          ...item,
          position: {
            ...position,
            zIndex: index + 1
          }
        };
      });
    } else {
      // Original overlapping polaroid style
      return items.map((item, index) => {
        const overlappingPositions = [
          { left: 50, top: 50, width: 200, height: 250, rotation: -5 },
          { left: 180, top: 80, width: 190, height: 240, rotation: 3 },
          { left: 350, top: 60, width: 200, height: 250, rotation: -2 },
          { left: 120, top: 280, width: 185, height: 230, rotation: 4 },
          { left: 320, top: 300, width: 195, height: 245, rotation: -3 },
          { left: 80, top: 450, width: 180, height: 220, rotation: 2 }
        ];
        
        const position = overlappingPositions[index] || {
          left: (index % 3) * 150 + Math.random() * 100,
          top: Math.floor(index / 3) * 200 + Math.random() * 80,
          width: 180 + Math.random() * 40,
          height: 220 + Math.random() * 50,
          rotation: (Math.random() - 0.5) * 10
        };
        
        return {
          ...item,
          position: {
            ...position,
            zIndex: index + 1
          }
        };
      });
    }
  };

  // Use improved positioning
  const positionedItems = generateBetterPositions(items);
  
  // Generate brand links for the outfit details
  const generateBrandLinks = () => {
    if (!items || items.length === 0) {
      return (
        <>
          <span className="category-name">Dress</span> 
          <a href="https://www.farfetch.com/search?q=floral+dress" target="_blank" rel="noopener noreferrer">Farfetch</a>
          ,&nbsp;
          <span className="category-name">Accessories</span> 
          <a href="https://www.nordstrom.com/browse/accessories" target="_blank" rel="noopener noreferrer">Nordstrom</a>
        </>
      );
    }
    
    // Group by category
    const categories = {};
    items.forEach(item => {
      const category = item.category || '';
      if (!categories[category]) {
        categories[category] = [];
      }
      categories[category].push(item);
    });
    
    return (
      <>
        {Object.keys(categories).map((category, index) => {
          const items = categories[category];
          const brand = items[0]?.brand || '';
          const url = items[0]?.productUrl || items[0]?.url || '';
          
          // Create search URL if direct URL not available
          const searchQuery = encodeURIComponent(`${brand} ${items[0]?.product_name || ''}`);
          
          // FARFETCH-FIRST: Use Farfetch for all categories, only exception for athletic brands
          const brandLower = brand.toLowerCase();
          const isAthletic = ['nike', 'adidas', 'under armour', 'lululemon', 'athleta'].some(b => brandLower.includes(b));
          const retailer = isAthletic ? 'Nordstrom' : 'Farfetch';
          const retailerUrl = retailer === 'Farfetch' 
            ? `https://www.farfetch.com/search?q=${searchQuery}`
            : `https://www.nordstrom.com/sr?keyword=${searchQuery}`;
          
          return (
            <React.Fragment key={category}>
              {index > 0 && ', '}
              <span className="category-name">{category}</span> 
              <a 
                href={url || retailerUrl} 
                target="_blank" 
                rel="noopener noreferrer"
              >
                {retailer}
              </a>
            </React.Fragment>
          );
        })}
      </>
    );
  };

  return (
    <div className="theme-collage-page">
      <div className="theme-collage-container">
        <h1 className="theme-collage-title">{title || "Date Night King 👑"}</h1>
        
        {/* Layout Toggle Controls */}
        <div className="layout-controls">
          <button 
            className={`layout-btn ${layoutStyle === 'scattered' ? 'active' : ''}`}
            onClick={() => setLayoutStyle('scattered')}
          >
            🎯 Clean Layout
          </button>
          <button 
            className={`layout-btn ${layoutStyle === 'overlapping' ? 'active' : ''}`}
            onClick={() => setLayoutStyle('overlapping')}
          >
            📸 Artistic Layout
          </button>
        </div>
        
        <div className="collage-carousel" style={{ backgroundColor: bgColor }}>
          <div className="h-fit w-full pb-24 pt-14">
            <div className="h-auto w-full">
              <div className="relative w-full overflow-hidden rounded-lg">
                {/* IMPROVED: Better collage container with controlled height */}
                <div style={{ height: '700px', backgroundColor: bgColor, position: 'relative' }}>
                  
                  {/* Map through positioned items */}
                  {positionedItems && positionedItems.map((item, index) => (
                    <div 
                      key={index}
                      className={`absolute cursor-pointer collage-item ${layoutStyle === 'overlapping' ? 'polaroid-style' : 'clean-style'}`}
                      style={{
                        left: `${item.position.left}px`,
                        top: `${item.position.top}px`,
                        width: `${item.position.width}px`,
                        height: `${item.position.height}px`,
                        zIndex: item.position.zIndex || 1,
                        transform: layoutStyle === 'overlapping' ? `rotate(${item.position.rotation || 0}deg)` : 'none'
                      }}
                      onClick={() => handleItemClick(item)}
                      role="button"
                      tabIndex={0}
                    >
                      {layoutStyle === 'overlapping' ? (
                        // Polaroid style with frame
                        <div className="polaroid-frame">
                          <img
                            alt={item.name || item.product_name || "Fashion item"}
                            crossOrigin="anonymous"
                            loading="lazy"
                            className="polaroid-image"
                            src={item.imageUrl || item.image_url}
                          />
                          <div className="polaroid-caption">
                            {item.product_name?.substring(0, 20) || `Item ${index + 1}`}
                          </div>
                        </div>
                      ) : (
                        // Clean style without frame
                        <img
                          alt={item.name || item.product_name || "Fashion item"}
                          crossOrigin="anonymous"
                          loading="lazy"
                          width={item.position.width}
                          height={item.position.height}
                          className="h-full w-full object-contain transition-all hover:scale-105 shadow-lg rounded-lg"
                          src={item.imageUrl || item.image_url}
                          style={{ color: 'transparent' }}
                        />
                      )}
                    </div>
                  ))}
                  
                  {/* Action buttons */}
                  <div className="absolute bottom-5 right-5 flex gap-2">
                    <button className="rounded-full bg-white p-2 shadow-md">
                      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" fill="none" stroke="currentColor" strokeWidth="2"/>
                      </svg>
                    </button>
                    <button className="rounded-full bg-white p-2 shadow-md">
                      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        <polyline points="16 6 12 2 8 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        <line x1="12" y1="2" x2="12" y2="15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        {/* Outfit details and price */}
        <div className="outfit-details">
          <h2 className="outfit-name">{outfitName}</h2>
          <div className="outfit-price">${totalPrice.toFixed(2)}</div>
          <p className="outfit-description">
            {description}
          </p>
          
          {/* Product links */}
          <div className="outfit-brands">
            {generateBrandLinks()}
          </div>
          
          {/* Tags */}
          <div className="outfit-tags">
            <button className="tag-button">date night</button>
          </div>
        </div>
      </div>
      
      <style jsx>{`
        .theme-collage-page {
          background-color: #fff;
          font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif;
        }
        
        .theme-collage-container {
          max-width: 1200px;
          margin: 0 auto;
          padding: 2rem;
        }
        
        .theme-collage-title {
          font-size: 2.5rem;
          font-weight: 700;
          margin-bottom: 1.5rem;
          text-align: center;
        }
        
        /* Layout Controls */
        .layout-controls {
          display: flex;
          justify-content: center;
          gap: 1rem;
          margin-bottom: 2rem;
        }
        
        .layout-btn {
          background-color: #f5f5f5;
          border: 2px solid #e0e0e0;
          color: #666;
          padding: 0.75rem 1.5rem;
          border-radius: 25px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.3s ease;
        }
        
        .layout-btn.active {
          background-color: #4a56e2;
          border-color: #4a56e2;
          color: white;
        }
        
        .layout-btn:hover {
          background-color: #e8e8e8;
        }
        
        .layout-btn.active:hover {
          background-color: #3a46d2;
        }
        
        .collage-carousel {
          border-radius: 1rem;
          overflow: hidden;
          position: relative;
          margin-bottom: 2rem;
        }
        
        /* IMPROVED: Better styling for collage items */
        .collage-item {
          transition: transform 0.3s ease, box-shadow 0.3s ease;
          border-radius: 8px;
          overflow: hidden;
        }
        
        .collage-item.clean-style:hover {
          transform: translateY(-5px) scale(1.02);
          box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
        }
        
        .collage-item.polaroid-style:hover {
          transform: translateY(-3px) scale(1.05);
          box-shadow: 0 12px 30px rgba(0, 0, 0, 0.2);
        }
        
        /* Polaroid Frame Style */
        .polaroid-frame {
          background-color: white;
          padding: 15px 15px 50px 15px;
          box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
          border-radius: 4px;
          width: 100%;
          height: 100%;
          display: flex;
          flex-direction: column;
        }
        
        .polaroid-image {
          width: 100%;
          flex: 1;
          object-fit: cover;
          border-radius: 2px;
        }
        
        .polaroid-caption {
          color: #333;
          font-size: 0.8rem;
          text-align: center;
          margin-top: 8px;
          font-family: 'Courier New', monospace;
        }
        
        .outfit-details {
          padding: 1.5rem;
          background-color: white;
          border-radius: 0.5rem;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        }
        
        .outfit-name {
          font-size: 1.8rem;
          font-weight: 600;
          margin: 0 0 0.5rem;
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
          margin-top: 1rem;
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
        
        /* Animations */
        @keyframes custom-bump-once {
          0% { transform: scale(1); }
          50% { transform: scale(1.05); }
          100% { transform: scale(1); }
        }
        
        .animate-custom-bump-once {
          animation: custom-bump-once 0.75s ease-in-out forwards;
        }
        
        /* Transitions */
        .transition-all {
          transition-property: all;
          transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
          transition-duration: 0.15s;
        }
        
        .hover\\:scale-105:hover {
          transform: scale(1.05);
        }
        
        /* Utility classes */
        .h-fit { height: fit-content; }
        .w-full { width: 100%; }
        .pb-24 { padding-bottom: 6rem; }
        .pt-14 { padding-top: 3.5rem; }
        .h-auto { height: auto; }
        .relative { position: relative; }
        .overflow-hidden { overflow: hidden; }
        .rounded-lg { border-radius: 0.5rem; }
        .absolute { position: absolute; }
        .bottom-5 { bottom: 1.25rem; }
        .right-5 { right: 1.25rem; }
        .flex { display: flex; }
        .gap-2 { gap: 0.5rem; }
        .rounded-full { border-radius: 9999px; }
        .bg-white { background-color: white; }
        .p-2 { padding: 0.5rem; }
        .shadow-md { box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); }
        .shadow-lg { box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05); }
        
        /* Responsive improvements */
        @media (max-width: 768px) {
          .collage-carousel > div > div > div > div {
            height: 500px !important;
          }
          
          .collage-item {
            width: 150px !important;
            height: 180px !important;
          }
          
          .layout-controls {
            flex-direction: column;
            align-items: center;
          }
          
          .layout-btn {
            width: 200px;
            text-align: center;
          }
        }
      `}</style>
    </div>
  );
};

export default ThemeCollage; 