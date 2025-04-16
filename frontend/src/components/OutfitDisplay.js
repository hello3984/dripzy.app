import React from 'react';
import OutfitCollage from './OutfitCollage';
import { getAffiliateUrl } from '../services/amazon';
import './OutfitDisplay.css';

/**
 * Displays a complete outfit with collage image and details
 */
const OutfitDisplay = ({ outfit, onTryOn }) => {
  if (!outfit) return null;

  // Format the price
  const formattedPrice = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2
  }).format(outfit.total_price);

  // Pass the entire outfit object to OutfitCollage for the new display style
  return (
    <div className="outfit-display">
      <OutfitCollage 
        collageImage={outfit.collage_image} 
        imageMap={outfit.image_map} 
        outfitName={outfit.name}
        outfit={outfit}
      />
      
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