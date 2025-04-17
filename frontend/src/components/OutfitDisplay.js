import React from 'react';
import OutfitCollage from './OutfitCollage';
import './OutfitDisplay.css';

/**
 * Displays a complete outfit with collage image and details
 */
const OutfitDisplay = ({ outfit, onTryOn }) => {
  if (!outfit) return null;

  // Format price for display
  // eslint-disable-next-line no-unused-vars
  const price = outfit.total_price ? new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2
  }).format(outfit.total_price) : '$0.00';

  // Pass the entire outfit object to OutfitCollage for the new display style
  return (
    <div className="outfit-display">
      <OutfitCollage 
        collageImage={outfit.collage_image} 
        imageMap={outfit.image_map} 
        outfitName={outfit.name}
        outfit={outfit}
      />
      
      <div className="ai-powered-badge">
        <span className="download-icon">⬇️</span> Powered by Dripzy AI
      </div>
      
      {onTryOn && (
        <div className="outfit-actions">
          <button 
            onClick={() => onTryOn(outfit)} 
            className="try-on-button"
          >
            Virtual Try-On
          </button>
        </div>
      )}
    </div>
  );
};

export default OutfitDisplay; 