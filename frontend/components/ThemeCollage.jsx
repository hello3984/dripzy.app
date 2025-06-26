import React, { useState, useEffect, useRef } from 'react';
import { getBestRetailUrl } from '../utils/retailUrlHelper';

const ThemeCollage = ({ title, items = [], style }) => {
  // Layout state - toggle between 'overlapping' and 'scattered'
  const [layoutStyle, setLayoutStyle] = useState('scattered'); // Default to cleaner layout
  const [containerDimensions, setContainerDimensions] = useState({ width: 800, height: 600 });
  const containerRef = useRef(null);
  
  // Update container dimensions on resize
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        setContainerDimensions({
          width: Math.max(rect.width, 600),
          height: Math.max(rect.height, 400)
        });
      }
    };
    
    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);
  
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
  
  // ADVANCED: Smart positioning with collision detection
  const generateSmartPositions = (items) => {
    if (!items || items.length === 0) return [];
    
    const { width: containerWidth, height: containerHeight } = containerDimensions;
    const isMobile = containerWidth < 768;
    
    // IMPROVED: Larger responsive item sizing with bigger gaps
    const baseItemWidth = isMobile ? 130 : 170;
    const baseItemHeight = isMobile ? 160 : 210;
    const minGap = isMobile ? 40 : 60; // INCREASED: Larger minimum gap between items
    
    const positions = [];
    const placedItems = [];
    
    // Helper function to check if position collides with existing items
    const hasCollision = (newPos, existingPositions, minGap) => {
      return existingPositions.some(pos => {
        const horizontalOverlap = newPos.left < pos.left + pos.width + minGap && 
                                 newPos.left + newPos.width + minGap > pos.left;
        const verticalOverlap = newPos.top < pos.top + pos.height + minGap && 
                               newPos.top + newPos.height + minGap > pos.top;
        return horizontalOverlap && verticalOverlap;
      });
    };
    
    // IMPROVED: More aggressive boundary checking with larger margins
    const isWithinBounds = (pos, containerWidth, containerHeight) => {
      const margin = isMobile ? 20 : 30;
      return pos.left >= margin && 
             pos.top >= margin && 
             pos.left + pos.width <= containerWidth - margin && 
             pos.top + pos.height <= containerHeight - margin;
    };
    
    if (layoutStyle === 'scattered') {
      // CLEAN SCATTERED LAYOUT - Gensmo style
      items.forEach((item, index) => {
        let attempts = 0;
        let position;
        
        do {
          // IMPROVED: Smaller size variations for more predictable layouts
          const widthVariation = Math.random() * 20 - 10; // ±10px (reduced)
          const heightVariation = Math.random() * 15 - 7; // ±7px (reduced)
          const margin = isMobile ? 20 : 30;
          
          position = {
            left: Math.random() * (containerWidth - baseItemWidth - margin * 2) + margin,
            top: Math.random() * (containerHeight - baseItemHeight - margin * 2) + margin,
            width: Math.max(baseItemWidth + widthVariation, baseItemWidth * 0.9),
            height: Math.max(baseItemHeight + heightVariation, baseItemHeight * 0.9),
            zIndex: index + 1,
            rotation: 0 // No rotation for clean layout
          };
          
          attempts++;
        } while (
          (hasCollision(position, placedItems, minGap) || !isWithinBounds(position, containerWidth, containerHeight)) && 
          attempts < 100 // INCREASED: More attempts for better positioning
        );
        
        // IMPROVED: More robust fallback grid positioning with padding
        if (attempts >= 100) {
          const cols = isMobile ? 2 : 3;
          const rows = Math.ceil(items.length / cols);
          const row = Math.floor(index / cols);
          const col = index % cols;
          
          // Add padding to prevent edge touching
          const padding = 20;
          const usableWidth = containerWidth - (padding * 2);
          const usableHeight = containerHeight - (padding * 2);
          const cellWidth = usableWidth / cols;
          const cellHeight = usableHeight / rows;
          
          // Calculate item size to fit in cell with gap
          const maxItemWidth = Math.min(cellWidth - minGap, baseItemWidth * 0.8);
          const maxItemHeight = Math.min(cellHeight - minGap, baseItemHeight * 0.8);
          
          position = {
            left: padding + col * cellWidth + (cellWidth - maxItemWidth) / 2,
            top: padding + row * cellHeight + (cellHeight - maxItemHeight) / 2,
            width: maxItemWidth,
            height: maxItemHeight,
            zIndex: index + 1,
            rotation: 0
          };
        }
        
        placedItems.push(position);
        positions.push({
          ...item,
          position
        });
      });
    } else {
      // ARTISTIC OVERLAPPING LAYOUT - Controlled overlap
      items.forEach((item, index) => {
        let attempts = 0;
        let position;
        
        do {
          const widthVariation = Math.random() * 30 - 15;
          const heightVariation = Math.random() * 25 - 12;
          
          position = {
            left: Math.random() * (containerWidth - baseItemWidth - 20) + 10,
            top: Math.random() * (containerHeight - baseItemHeight - 20) + 10,
            width: baseItemWidth + widthVariation,
            height: baseItemHeight + heightVariation,
            zIndex: index + 1,
            rotation: (Math.random() - 0.5) * 8 // Subtle rotation ±4 degrees
          };
          
          attempts++;
        } while (
          (hasCollision(position, placedItems, minGap * 0.5) || !isWithinBounds(position, containerWidth, containerHeight)) && 
          attempts < 80 // IMPROVED: More attempts with slightly more overlap allowed for artistic style
        );
        
        // IMPROVED: Better controlled fallback with artistic positioning
        if (attempts >= 80) {
          const cols = isMobile ? 2 : 3;
          const rows = Math.ceil(items.length / cols);
          const row = Math.floor(index / cols);
          const col = index % cols;
          
          const padding = 30;
          const usableWidth = containerWidth - (padding * 2);
          const usableHeight = containerHeight - (padding * 2);
          const cellWidth = usableWidth / cols;
          const cellHeight = usableHeight / rows;
          
          // Add some artistic randomness but keep within bounds
          const randomX = (Math.random() - 0.5) * 40; // ±20px variation
          const randomY = (Math.random() - 0.5) * 30; // ±15px variation
          
          position = {
            left: Math.max(padding, Math.min(
              padding + col * cellWidth + (cellWidth - baseItemWidth) / 2 + randomX,
              containerWidth - baseItemWidth - padding
            )),
            top: Math.max(padding, Math.min(
              padding + row * cellHeight + (cellHeight - baseItemHeight) / 2 + randomY,
              containerHeight - baseItemHeight - padding
            )),
            width: baseItemWidth * 0.95,
            height: baseItemHeight * 0.95,
            zIndex: index + 1,
            rotation: (Math.random() - 0.5) * 4 // Reduced rotation for better control
          };
        }
        
        placedItems.push(position);
        positions.push({
          ...item,
          position
        });
      });
    }
    
    return positions;
  };

  // Use smart positioning
  const positionedItems = generateSmartPositions(items);
  
  // Calculate responsive container height
  const getContainerHeight = () => {
    if (containerDimensions.width < 768) return '500px'; // Mobile
    if (containerDimensions.width < 1024) return '600px'; // Tablet
    return '700px'; // Desktop
  };
  
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
                {/* SMART: Responsive collage container */}
                <div 
                  ref={containerRef}
                  style={{ 
                    height: getContainerHeight(), 
                    backgroundColor: bgColor, 
                    position: 'relative',
                    minHeight: '400px'
                  }}
                >
                  
                  {/* Map through smartly positioned items */}
                  {positionedItems && positionedItems.map((item, index) => (
                    <div 
                      key={index}
                      className={`absolute cursor-pointer collage-item ${layoutStyle === 'overlapping' ? 'polaroid-style' : 'clean-style'}`}
                      style={{
                        left: `${Math.max(0, Math.min(item.position.left, containerDimensions.width - item.position.width))}px`,
                        top: `${Math.max(0, Math.min(item.position.top, containerDimensions.height - item.position.height))}px`,
                        width: `${item.position.width}px`,
                        height: `${item.position.height}px`,
                        zIndex: item.position.zIndex || 1,
                        transform: `rotate(${item.position.rotation || 0}deg)`
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
                        <div className="clean-item-container">
                          <img
                            alt={item.name || item.product_name || "Fashion item"}
                            crossOrigin="anonymous"
                            loading="lazy"
                            className="clean-item-image"
                            src={item.imageUrl || item.image_url}
                          />
                          <div className="clean-item-overlay">
                            <div className="item-price">${item.price || '0.00'}</div>
                            <div className="item-brand">{item.brand || 'Brand'}</div>
                          </div>
                        </div>
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
        
        /* SMART: Enhanced collage items with no overlap issues */
        .collage-item {
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          border-radius: 8px;
          overflow: hidden;
          will-change: transform;
        }
        
        .collage-item.clean-style:hover {
          transform: translateY(-8px) scale(1.05) !important;
          box-shadow: 0 15px 35px rgba(0, 0, 0, 0.15);
          z-index: 1000 !important;
        }
        
        .collage-item.polaroid-style:hover {
          transform: translateY(-5px) scale(1.03) rotate(0deg) !important;
          box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
          z-index: 1000 !important;
        }
        
        /* Clean Item Style */
        .clean-item-container {
          position: relative;
          width: 100%;
          height: 100%;
          border-radius: 12px;
          overflow: hidden;
          background: white;
          box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }
        
        .clean-item-image {
          width: 100%;
          height: 85%;
          object-fit: cover;
          border-radius: 12px 12px 0 0;
        }
        
        .clean-item-overlay {
          position: absolute;
          bottom: 0;
          left: 0;
          right: 0;
          background: white;
          padding: 8px 12px;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        
        .item-price {
          font-weight: 700;
          color: #ff6b6b;
          font-size: 0.9rem;
        }
        
        .item-brand {
          font-size: 0.8rem;
          color: #666;
          text-transform: uppercase;
        }
        
        /* Polaroid Frame Style */
        .polaroid-frame {
          background-color: white;
          padding: 15px 15px 45px 15px;
          box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
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
          font-size: 0.75rem;
          text-align: center;
          margin-top: 8px;
          font-family: 'Courier New', monospace;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
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
        
        /* RESPONSIVE: Smart mobile adaptations */
        @media (max-width: 768px) {
          .theme-collage-container {
            padding: 1rem;
          }
          
          .theme-collage-title {
            font-size: 1.8rem;
          }
          
          .layout-controls {
            gap: 0.5rem;
          }
          
          .layout-btn {
            padding: 0.5rem 1rem;
            font-size: 0.9rem;
          }
          
          .collage-item {
            min-width: 120px !important;
            min-height: 150px !important;
          }
          
          .polaroid-frame {
            padding: 10px 10px 35px 10px;
          }
          
          .polaroid-caption {
            font-size: 0.7rem;
          }
          
          .clean-item-overlay {
            padding: 6px 8px;
          }
          
          .item-price {
            font-size: 0.8rem;
          }
          
          .item-brand {
            font-size: 0.7rem;
          }
        }
        
        @media (max-width: 480px) {
          .theme-collage-title {
            font-size: 1.5rem;
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