import React from 'react';
import { getBestRetailUrl } from '../utils/retailUrlHelper';

const ThemeCollage = ({ title, items = [], style }) => {
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
          const isAthletic = [
            'nike', 'adidas', 'under armour', 'lululemon', 'athleta', 'reebok',
            'alo yoga', 'alo', 'outdoor voices', 'set active', 'girlfriend collective',
            'beyond yoga', 'vuori', 'fabletics', 'spiritual gangster', 'puma', 
            'new balance', 'asics', 'brooks', 'hoka', 'on running', 'on'
          ].some(b => brandLower.includes(b));
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
        
        <div className="collage-carousel" style={{ backgroundColor: bgColor }}>
          <div className="h-fit w-full pb-24 pt-14">
            <div className="h-auto w-full">
              <div className="relative w-full overflow-hidden rounded-lg">
                {/* Main collage container with absolute positioning */}
                <div style={{ height: '1358px', backgroundColor: bgColor }}>
                  
                  {/* Map through items and position them absolutely */}
                  {items && items.map((item, index) => (
                    <div 
                      key={index}
                      className="absolute cursor-pointer" 
                      style={{
                        left: `${item.position.left}px`,
                        top: `${item.position.top}px`,
                        width: `${item.position.width}px`,
                        height: `${item.position.height}px`,
                        zIndex: item.position.zIndex || 1
                      }}
                      onClick={() => handleItemClick(item)}
                      role="button"
                      tabIndex={0}
                    >
                      <img
                        alt={item.name || item.product_name || "Fashion item"}
                        crossOrigin="anonymous"
                        loading="lazy"
                        width={item.position.width}
                        height={item.position.height}
                        className="h-full w-full object-contain animate-custom-bump-once transition-all hover:scale-110"
                        src={item.imageUrl || item.image_url}
                        style={{ color: 'transparent' }}
                      />
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
        
        .collage-carousel {
          border-radius: 1rem;
          overflow: hidden;
          position: relative;
          margin-bottom: 2rem;
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
        
        .hover\\:scale-110:hover {
          transform: scale(1.1);
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
      `}</style>
    </div>
  );
};

export default ThemeCollage; 