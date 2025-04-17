import React, { useState } from 'react';
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
  const [imageError, setImageError] = useState(false);

  // Handler for image loading errors
  const handleImageError = (e) => {
    console.log("Error loading image, using fallback");
    setImageError(true);
    // Set a default placeholder image
    e.target.src = "https://via.placeholder.com/800x600?text=Outfit+Collage";
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
    
    return (
      <div className="styled-outfit-collage">
        <div className="outfit-occasion">
          <span className="occasion-tag">{outfit.occasion || "Weekend"}</span>
        </div>
        
        <div className="outfit-items-grid">
          {items.map((item, index) => (
            <div 
              key={item.product_id || index} 
              className={`outfit-item-card ${item.category.toLowerCase()}`}
              onClick={() => window.open(item.url, '_blank', 'noopener,noreferrer')}
            >
              <div className="item-image-container">
                <img 
                  src={item.image_url || "https://via.placeholder.com/400x600?text=Product+Image"} 
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
          ))}
          
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
          
          <div className="outfit-brands">
            {Object.entries(brandsByCategory).map(([category, brands], index) => (
              <div key={category} className="brand-category">
                <span className="category-name">{category}</span> {brands}
                {index !== Object.entries(brandsByCategory).length - 1 && <span className="brand-separator">,</span>}
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Fallback to old collage if individual items aren't available
  if (!collageImage && !imageError) {
    return (
      <div className="outfit-collage-placeholder">
        <p>No collage available</p>
      </div>
    );
  }

  // Ensure the image has the proper data URL format
  let imageSource = imageError 
    ? "https://via.placeholder.com/800x600?text=Outfit+Collage" 
    : (collageImage?.startsWith('data:') 
      ? collageImage 
      : (collageImage?.startsWith('http') 
          ? collageImage 
          : `data:image/png;base64,${collageImage}`));

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
          src={imageSource} 
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
          {imageMap && imageMap.map((item, index) => (
            <area
              key={index}
              alt={`${item.category} item`}
              title={`Shop ${item.category}`}
              shape="rect"
              coords={item.coords?.join(',') || "0,0,0,0"}
              onClick={() => handleAreaClick(item.url)}
              onMouseEnter={() => handleMouseEnter(item)}
              onMouseLeave={handleMouseLeave}
              style={{ cursor: item.url && item.url !== '#' ? 'pointer' : 'default' }}
            />
          ))}
        </map>
      </div>
      
      {/* Category labels under the collage */}
      <div className="outfit-collage-categories">
        {imageMap && [...new Set(imageMap.map(item => item.category))].map((category, index) => (
          <span key={index} className="category-label">
            {category}
          </span>
        ))}
      </div>
    </div>
  );
};

export default OutfitCollage; 