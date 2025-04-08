import React from 'react';
import OutfitCollage from './OutfitCollage';
import { getAffiliateUrl } from '../services/amazon';

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

  // Check if we have a collage image and image map
  const hasCollage = outfit.collage_image && outfit.image_map && outfit.image_map.length > 0;

  return (
    <div className="outfit-display">
      <h3 className="outfit-name">{outfit.name}</h3>
      <div className="outfit-price">{formattedPrice}</div>
      
      <p className="outfit-description">{outfit.description}</p>
      
      {hasCollage ? (
        <OutfitCollage 
          collageImage={outfit.collage_image} 
          imageMap={outfit.image_map}
          outfitName={outfit.name}
        />
      ) : (
        <div className="outfit-items-grid">
          {outfit.items && outfit.items.map((item, index) => (
            <div className="outfit-item" key={index}>
              <div className="item-image">
                <img 
                  src={item.image_url || 'https://via.placeholder.com/300x400'} 
                  alt={item.product_name}
                  onError={(e) => {
                    e.target.onerror = null;
                    e.target.src = 'https://via.placeholder.com/300x400';
                  }}
                />
              </div>
              <div className="item-details">
                <div className="item-category">{item.category}</div>
                <h4 className="item-name">{item.product_name}</h4>
                <div className="item-brand">{item.brand}</div>
                <div className="item-price">
                  {new Intl.NumberFormat('en-US', {
                    style: 'currency',
                    currency: 'USD'
                  }).format(item.price)}
                </div>
                <a 
                  href={getAffiliateUrl(item.url, item.brand)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="shop-now-button"
                >
                  Shop Now
                </a>
              </div>
            </div>
          ))}
        </div>
      )}
      
      {/* Brands display */}
      {outfit.brand_display && (
        <div className="brand-display">
          {Object.entries(outfit.brand_display).map(([category, brands], index) => (
            <div key={index} className="brand-category">
              <span className="brand-category-name">{category}:</span> {brands}
            </div>
          ))}
        </div>
      )}
      
      {/* Try-on button */}
      {onTryOn && (
        <button 
          className="try-on-button" 
          onClick={onTryOn}
        >
          Virtual Try-On
        </button>
      )}
    </div>
  );
};

export default OutfitDisplay; 