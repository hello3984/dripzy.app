import React from 'react';

const OutfitDisplay = ({ outfit, onTryOn }) => {
  if (!outfit || !outfit.items || outfit.items.length === 0) {
    return <div className="outfit-empty">No outfit data available</div>;
  }

  const { items, total_price, style_description, outfit_name } = outfit;

  return (
    <div className="outfit-display">
      <div className="outfit-header">
        <h3 className="outfit-name">{outfit_name}</h3>
        <span className="outfit-price">${total_price.toFixed(2)}</span>
      </div>
      
      <p className="outfit-description">{style_description}</p>
      
      <div className="outfit-items">
        {items.map((item, index) => (
          <div className="outfit-item" key={index}>
            <div className="item-image">
              <img src={item.image_url} alt={item.name} onError={(e) => {
                e.target.onerror = null;
                e.target.src = 'https://via.placeholder.com/150?text=No+Image';
              }} />
            </div>
            <div className="item-details">
              <h4 className="item-name">{item.name}</h4>
              <p className="item-brand">{item.brand}</p>
              <p className="item-price">${item.price.toFixed(2)}</p>
              <p className="item-description">{item.description}</p>
              <a href={item.url} target="_blank" rel="noopener noreferrer" className="item-link">
                Shop Item
              </a>
            </div>
          </div>
        ))}
      </div>
      
      <div className="outfit-actions">
        <button className="try-on-button" onClick={() => onTryOn(outfit)}>
          Try On This Outfit
        </button>
        <button className="save-button">
          Save Outfit
        </button>
      </div>
    </div>
  );
};

export default OutfitDisplay; 