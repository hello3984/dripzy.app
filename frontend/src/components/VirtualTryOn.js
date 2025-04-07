import React, { useState } from 'react';

const VirtualTryOn = ({ outfit, avatarType, onClose }) => {
  const [loading, setLoading] = useState(false);
  const [tryOnImage, setTryOnImage] = useState(null);
  const [error, setError] = useState(null);

  const generateTryOn = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // In a real implementation, this would call the backend API
      // const response = await fetch('http://localhost:8000/tryon/generate', {
      //   method: 'POST',
      //   headers: {
      //     'Content-Type': 'application/json',
      //   },
      //   body: JSON.stringify({
      //     outfit_items: outfit.items,
      //     avatar_type: avatarType,
      //     gender: 'neutral'
      //   }),
      // });
      
      // if (!response.ok) {
      //   throw new Error('Failed to generate try-on image');
      // }
      
      // const data = await response.json();
      // setTryOnImage(data.image_base64);
      
      // Mock response for demonstration
      setTimeout(() => {
        // Use a placeholder image for the demo
        setTryOnImage('https://via.placeholder.com/400x600?text=Virtual+Try+On+Demo');
        setLoading(false);
      }, 2000);
    } catch (err) {
      setError(err.message || 'Failed to generate try-on image');
      setLoading(false);
    }
  };

  // Generate the try-on image when the component mounts
  React.useEffect(() => {
    generateTryOn();
  }, []);

  return (
    <div className="virtual-tryon-modal">
      <div className="tryon-header">
        <h2>Virtual Try-On</h2>
        <button className="close-button" onClick={onClose}>×</button>
      </div>
      
      <div className="tryon-content">
        {loading ? (
          <div className="loading-indicator">
            <p>Generating your virtual try-on...</p>
            <div className="spinner"></div>
          </div>
        ) : error ? (
          <div className="error-message">
            <p>Error: {error}</p>
            <button onClick={generateTryOn}>Try Again</button>
          </div>
        ) : tryOnImage ? (
          <div className="tryon-result">
            <div className="tryon-image">
              <img 
                src={tryOnImage.startsWith('data:') ? tryOnImage : tryOnImage} 
                alt="Virtual try-on" 
              />
            </div>
            
            <div className="outfit-summary">
              <h3>{outfit.outfit_name}</h3>
              <p>{outfit.style_description}</p>
              <p className="price-tag">Total: ${outfit.total_price.toFixed(2)}</p>
              
              <div className="outfit-items-summary">
                {outfit.items.map((item, index) => (
                  <div className="summary-item" key={index}>
                    <span className="item-name">{item.name}</span>
                    <span className="item-price">${item.price.toFixed(2)}</span>
                  </div>
                ))}
              </div>
              
              <div className="tryon-actions">
                <button className="shop-all-button">Shop All Items</button>
                <button className="share-button">Share Look</button>
              </div>
            </div>
          </div>
        ) : (
          <div className="no-result">
            <p>No try-on image available.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default VirtualTryOn; 