import React, { useState, useEffect } from 'react';
import './OutfitCollage.css';

/**
 * OutfitCollage component - displays a collage image with clickable areas
 * @param {Object} props
 * @param {string} props.collageImage - Base64 encoded image
 * @param {Array} props.imageMap - Array of clickable areas with coords, category, url
 * @param {string} props.outfitName - Name of the outfit
 * @param {Object} props.outfit - Complete outfit data
 */
const OutfitCollage = ({ collageImage, imageMap, outfitName, outfit }) => {
  const [hoveredItem, setHoveredItem] = useState(null);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [collageImageSrc, setCollageImageSrc] = useState('');

  // Process collage image on component mount or when props change
  useEffect(() => {
    if (collageImage) {
      // Process the image source - handle base64 and URL formats
      let imageSource = collageImage?.startsWith('data:') 
        ? collageImage 
        : (collageImage?.startsWith('http') 
            ? collageImage 
            : `data:image/png;base64,${collageImage}`);
      
      // Avoid any references to placeholder domains
      if (!imageSource.includes('placeholder') && 
          !imageSource.includes('example.com') && 
          !imageSource.includes('unsplash')) {
        setCollageImageSrc(imageSource);
        setImageLoaded(true);
      } else {
        setImageLoaded(false);
      }
    } else {
      setImageLoaded(false);
    }
  }, [collageImage]);

  // Handler for image loading errors - simply hide the element
  const handleImageError = (e) => {
            // Error loading image, element will be hidden
    e.target.style.display = 'none';
    e.target.parentNode.classList.add('image-load-error');
  };

  // If individual product images are available, use those instead of the collage
  if (outfit && outfit.items && outfit.items.length > 0) {
    const items = outfit.items;
    
    // Group items by category
    const categories = {
      "Top": items.filter(item => item.category === "Top"),
      "Bottom": items.filter(item => item.category === "Bottom" || item.category === "Bottoms"),
      "Dress": items.filter(item => item.category === "Dress"),
      "Shoes": items.filter(item => item.category === "Shoes"),
      "Accessory": items.filter(item => 
        item.category === "Accessory" || 
        item.category === "Accessories" || 
        item.category === "Bag" || 
        item.category === "Hat"
      ),
      "Outerwear": items.filter(item => item.category === "Outerwear"),
    };
    
    // Format brand text display
    const brandsByCategory = {};
    Object.keys(categories).forEach(category => {
      if (categories[category].length > 0) {
        const brands = [...new Set(categories[category].map(item => item.brand))];
        const pluralCategory = category === "Accessory" ? "Accessories" : 
                              category.endsWith('s') ? category : `${category}s`;
        brandsByCategory[pluralCategory] = brands.join(', ');
      }
    });
    
    // Filter out items with invalid image URLs
    const validItems = items.filter(item => 
      item.image_url && 
      !item.image_url.includes('placeholder') && 
      !item.image_url.includes('example.com') &&
      !item.image_url.includes('unsplash') &&
      !item.image_url.includes('via.placeholder')
    );
    
    // Only render if we have valid items
    if (validItems.length > 0) {
      return (
        <div className="styled-outfit-collage">
          <div className="outfit-occasion">
            <span className="occasion-tag">{outfit.occasion || "Weekend"}</span>
          </div>
          
          <div className="outfit-items-grid">
            {validItems.map((item, index) => {
              // Create search query
              const searchQuery = encodeURIComponent(`${item.brand || ''} ${item.product_name || ''}`).trim();
              
              // Create Farfetch URL as primary option
              const farfetchUrl = `https://www.farfetch.com/search?q=${searchQuery}`;
              const nordstromUrl = `https://www.nordstrom.com/sr?keyword=${searchQuery}`;
              
              // FARFETCH-FIRST: Use Farfetch for all items, only exception for athletic brands
              const brand = (item.brand || '').toLowerCase();
              const isAthletic = ['nike', 'adidas', 'under armour', 'lululemon', 'athleta'].some(b => brand.includes(b));
              const retailerUrl = isAthletic ? nordstromUrl : farfetchUrl;
              
              // Use item URL if available, otherwise use the retailer URL
              const finalUrl = item.url || retailerUrl;
              
              return (
                <div 
                  key={item.product_id || index} 
                  className={`outfit-item-card ${item.category.toLowerCase()}`}
                  onClick={() => window.open(finalUrl, '_blank', 'noopener,noreferrer')}
                >
                  <div className="item-image-container">
                    <img 
                      src={item.image_url} 
                      alt={item.product_name || "Fashion item"} 
                      className="item-image"
                      onError={handleImageError}
                    />
                    <button className="favorite-button">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
                      </svg>
                    </button>
                  </div>
                </div>
              );
            })}
            
            <button className="share-button">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"></path>
                <polyline points="16 6 12 2 8 6"></polyline>
                <line x1="12" y1="2" x2="12" y2="15"></line>
              </svg>
            </button>
          </div>
          
          <div className="outfit-details">
            <h2 className="outfit-name">{outfitName || "Stylish Outfit"}</h2>
            <div className="outfit-price">${outfit.total_price ? outfit.total_price.toFixed(2) : "0.00"}</div>
            <p className="outfit-description">{outfit.description || "A perfectly curated outfit for your style."}</p>
            
            {/* Updated brands section with direct links to Nordstrom/Farfetch */}
            <div className="outfit-brands">
              {(() => {
                // Build direct HTML links with retailer alternation
                let brandsHtml = '';
                const categories = Object.keys(brandsByCategory);
                
                categories.forEach((category, categoryIndex) => {
                  // Add category name
                  brandsHtml += categoryIndex === 0 ? '' : ', ';
                  brandsHtml += `<span class="category-name">${category}</span> `;
                  
                  // Get related items for this category
                  const itemsInCategory = validItems.filter(item => {
                    const itemCategory = item.category || '';
                    const pluralCategory = itemCategory === "Accessory" ? "Accessories" : 
                                          itemCategory.endsWith('s') ? itemCategory : `${itemCategory}s`;
                    return pluralCategory.toLowerCase() === category.toLowerCase();
                  });
                  
                  // Create search query from first item in category
                  const firstItem = itemsInCategory[0] || {};
                  const searchQuery = encodeURIComponent(`${firstItem.brand || ''} ${firstItem.product_name || ''}`).trim();
                  
                  // FARFETCH-FIRST: Use Farfetch for all categories, only exception for athletic brands
                  const brand = (firstItem.brand || '').toLowerCase();
                  const isAthletic = ['nike', 'adidas', 'under armour', 'lululemon', 'athleta'].some(b => brand.includes(b));
                  const retailer = isAthletic ? 'Nordstrom' : 'Farfetch';
                  
                  // Create retailer URL
                  const retailerUrl = retailer === 'Nordstrom' 
                    ? `https://www.nordstrom.com/sr?keyword=${searchQuery}`
                    : `https://www.farfetch.com/search?q=${searchQuery}`;
                  
                  // Add retailer link
                  brandsHtml += `<a href="${retailerUrl}" target="_blank" rel="noopener noreferrer" style="color:#0066cc; text-decoration:underline; cursor:pointer;">${retailer}</a>`;
                });
                
                return (
                  <div dangerouslySetInnerHTML={{ __html: brandsHtml }} />
                );
              })()}
            </div>
          </div>
        </div>
      );
    }
  }

  // Display loading state if no valid images are available
  if (!imageLoaded || !collageImageSrc) {
    return (
      <div className="outfit-collage-placeholder">
        <p>Generating outfit pieces that match your style...</p>
      </div>
    );
  }

  // Only show valid image maps (filter out any with placeholder URLs)
  const validImageMap = imageMap?.filter(item => 
    item.url && 
    item.url !== '#' && 
    !item.url.includes('placeholder') && 
    !item.url.includes('via.placeholder') &&
    !item.url.includes('example.com') &&
    !item.url.includes('unsplash')
  ) || [];

  // Handle mouse enter on an area
  const handleMouseEnter = (item) => {
    setHoveredItem(item);
  };

  // Handle mouse leave
  const handleMouseLeave = () => {
    setHoveredItem(null);
  };

  // Handle click on an area
  const handleAreaClick = (url) => {
    if (url && url !== '#') {
      window.open(url, '_blank', 'noopener,noreferrer');
    }
  };

  return (
    <div className="outfit-collage-container">
      <h3 className="outfit-collage-title">{outfitName || 'Outfit Collage'}</h3>
      
      <div className="outfit-collage-image-container">
        <img 
          src={collageImageSrc} 
          alt={outfitName || 'Outfit Collage'} 
          className="outfit-collage-image" 
          useMap="#outfitMap"
          onError={handleImageError}
        />
        
        {/* Overlay for hovered item */}
        {hoveredItem && (
          <div 
            className="outfit-collage-hover-overlay"
            style={{
              left: hoveredItem.coords[0],
              top: hoveredItem.coords[1],
              width: hoveredItem.coords[2] - hoveredItem.coords[0],
              height: hoveredItem.coords[3] - hoveredItem.coords[1]
            }}
          >
            <div className="hover-content">
              <p>Shop {hoveredItem.category}</p>
            </div>
          </div>
        )}
        
        {/* Create the map and areas */}
        <map name="outfitMap">
          {validImageMap.map((item, index) => (
            <area
              key={index}
              alt={`${item.category} item`}
              title={`Shop ${item.category}`}
              shape="rect"
              coords={item.coords?.join(',') || "0,0,0,0"}
              onClick={() => handleAreaClick(item.url)}
              onMouseEnter={() => handleMouseEnter(item)}
              onMouseLeave={handleMouseLeave}
              style={{ cursor: 'pointer' }}
            />
          ))}
        </map>
      </div>
      
      {/* Category labels under the collage - only show categories with valid URLs */}
      <div className="outfit-collage-categories">
        {validImageMap.length > 0 && 
          [...new Set(validImageMap.map(item => item.category))].map((category, index) => (
            <span key={index} className="category-label">
              {category}
            </span>
          ))
        }
      </div>
    </div>
  );
};

export default OutfitCollage; 