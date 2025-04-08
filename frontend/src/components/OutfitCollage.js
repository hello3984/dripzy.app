import React, { useState } from 'react';
import './OutfitCollage.css';

/**
 * OutfitCollage component - displays a collage image with clickable areas
 * @param {Object} props
 * @param {string} props.collageImage - Base64 encoded image
 * @param {Array} props.imageMap - Array of clickable areas with coords, category, url
 * @param {string} props.outfitName - Name of the outfit
 */
const OutfitCollage = ({ collageImage, imageMap, outfitName }) => {
  const [hoveredItem, setHoveredItem] = useState(null);

  if (!collageImage) {
    return (
      <div className="outfit-collage-placeholder">
        <p>No collage available</p>
      </div>
    );
  }

  // Ensure the image has the proper data URL format
  const imageSource = collageImage.startsWith('data:') 
    ? collageImage 
    : `data:image/png;base64,${collageImage}`;

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
              coords={item.coords.join(',')}
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