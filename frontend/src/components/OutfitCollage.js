import React from 'react';
import './OutfitCollage.css';

const OutfitCollage = ({ collageImage, imageMap }) => {
  if (!collageImage) {
    return <div className="collage-placeholder">No collage available</div>;
  }

  return (
    <div className="outfit-collage-container">
      <div className="collage-image-container">
        <img src={collageImage} alt="Outfit Collage" className="collage-image" />
        
        {/* Create clickable areas over the image */}
        {imageMap && imageMap.map((area, index) => (
          <a 
            key={index}
            href={area.url}
            target="_blank"
            rel="noopener noreferrer"
            className="collage-clickable-area"
            style={{
              position: 'absolute',
              left: `${area.coords.x1}px`,
              top: `${area.coords.y1}px`,
              width: `${area.coords.x2 - area.coords.x1}px`,
              height: `${area.coords.y2 - area.coords.y1}px`
            }}
            title={`Shop ${area.category}`}
          >
            <div className="area-hover-overlay">
              <span className="shop-text">Shop {area.category}</span>
            </div>
          </a>
        ))}
      </div>
      <p className="collage-instructions">Click on any item to shop</p>
    </div>
  );
};

export default OutfitCollage; 