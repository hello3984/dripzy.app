import React, { useState, useRef, useEffect } from 'react';

const VirtualTryOn = ({ outfit, avatarType, onClose, userImage }) => {
  const [loading, setLoading] = useState(false);
  const [tryOnImage, setTryOnImage] = useState(null);
  const [error, setError] = useState(null);
  const [selectedItem, setSelectedItem] = useState(null);
  const [clothingItems, setClothingItems] = useState([]);
  const canvasRef = useRef(null);
  const containerRef = useRef(null);

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
        // Use a placeholder image for the demo or the user's uploaded image
        setTryOnImage(userImage || 'https://via.placeholder.com/400x600?text=Virtual+Try+On+Demo');
        
        // Create mock clothing items for overlay
        if (outfit && outfit.items) {
          const initialItems = outfit.items.map((item, index) => ({
            id: item.id || `item-${index}`,
            name: item.name,
            imageUrl: item.image_url || `https://via.placeholder.com/200x200?text=${encodeURIComponent(item.name)}`,
            position: { x: 150 + (index * 20), y: 200 + (index * 30) },
            size: { width: 200, height: 200 },
            rotation: 0,
            zIndex: index + 1,
            category: item.category
          }));
          setClothingItems(initialItems);
        }
        
        setLoading(false);
      }, 2000);
    } catch (err) {
      setError(err.message || 'Failed to generate try-on image');
      setLoading(false);
    }
  };

  // Generate the try-on image when the component mounts
  useEffect(() => {
    generateTryOn();
  }, []);

  // Handle mouse interactions for dragging clothing items
  const handleMouseDown = (e, item) => {
    e.preventDefault();
    setSelectedItem(item);
    
    const containerRect = containerRef.current.getBoundingClientRect();
    const startX = e.clientX - containerRect.left;
    const startY = e.clientY - containerRect.top;
    const startItemX = item.position.x;
    const startItemY = item.position.y;
    
    const handleMouseMove = (moveEvent) => {
      const currentX = moveEvent.clientX - containerRect.left;
      const currentY = moveEvent.clientY - containerRect.top;
      const deltaX = currentX - startX;
      const deltaY = currentY - startY;
      
      setClothingItems(items => 
        items.map(clothingItem => 
          clothingItem.id === item.id 
            ? {
                ...clothingItem,
                position: {
                  x: startItemX + deltaX,
                  y: startItemY + deltaY
                }
              }
            : clothingItem
        )
      );
    };
    
    const handleMouseUp = () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
    
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };

  // Handle resizing of clothing items
  const handleResize = (e, item, corner) => {
    e.preventDefault();
    e.stopPropagation();
    
    const containerRect = containerRef.current.getBoundingClientRect();
    const startX = e.clientX - containerRect.left;
    const startY = e.clientY - containerRect.top;
    const startWidth = item.size.width;
    const startHeight = item.size.height;
    
    const handleMouseMove = (moveEvent) => {
      const currentX = moveEvent.clientX - containerRect.left;
      const currentY = moveEvent.clientY - containerRect.top;
      const deltaX = currentX - startX;
      const deltaY = currentY - startY;
      
      let newWidth = startWidth;
      let newHeight = startHeight;
      
      // Adjust size based on which corner is being dragged
      if (corner === 'se') {
        newWidth = Math.max(50, startWidth + deltaX);
        newHeight = Math.max(50, startHeight + deltaY);
      } else if (corner === 'sw') {
        newWidth = Math.max(50, startWidth - deltaX);
        newHeight = Math.max(50, startHeight + deltaY);
      } else if (corner === 'ne') {
        newWidth = Math.max(50, startWidth + deltaX);
        newHeight = Math.max(50, startHeight - deltaY);
      } else if (corner === 'nw') {
        newWidth = Math.max(50, startWidth - deltaX);
        newHeight = Math.max(50, startHeight - deltaY);
      }
      
      // Update the item size
      setClothingItems(items => 
        items.map(clothingItem => 
          clothingItem.id === item.id 
            ? {
                ...clothingItem,
                size: {
                  width: newWidth,
                  height: newHeight
                }
              }
            : clothingItem
        )
      );
    };
    
    const handleMouseUp = () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
    
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };

  // Handle rotation of clothing items
  const handleRotate = (e, item) => {
    e.preventDefault();
    e.stopPropagation();
    
    const containerRect = containerRef.current.getBoundingClientRect();
    const centerX = item.position.x + item.size.width / 2;
    const centerY = item.position.y + item.size.height / 2;
    
    const startAngle = Math.atan2(
      e.clientY - containerRect.top - centerY,
      e.clientX - containerRect.left - centerX
    );
    
    const startRotation = item.rotation;
    
    const handleMouseMove = (moveEvent) => {
      const currentAngle = Math.atan2(
        moveEvent.clientY - containerRect.top - centerY,
        moveEvent.clientX - containerRect.left - centerX
      );
      
      const angleDiff = (currentAngle - startAngle) * (180 / Math.PI);
      
      setClothingItems(items => 
        items.map(clothingItem => 
          clothingItem.id === item.id 
            ? {
                ...clothingItem,
                rotation: (startRotation + angleDiff) % 360
              }
            : clothingItem
        )
      );
    };
    
    const handleMouseUp = () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
    
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };

  // Handle click on background to deselect items
  const handleCanvasClick = (e) => {
    if (e.target === containerRef.current) {
      setSelectedItem(null);
    }
  };

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
            <div className="tryon-canvas-container" ref={containerRef} onClick={handleCanvasClick}>
              <div 
                className="tryon-canvas" 
                ref={canvasRef}
                style={{
                  backgroundImage: `url(${tryOnImage})`,
                  backgroundSize: 'contain',
                  backgroundPosition: 'center',
                  backgroundRepeat: 'no-repeat',
                  position: 'relative',
                  width: '100%',
                  height: '600px'
                }}
              >
                {clothingItems.map((item) => (
                  <div
                    key={item.id}
                    className={`clothing-item ${selectedItem && selectedItem.id === item.id ? 'selected' : ''}`}
                    style={{
                      position: 'absolute',
                      left: `${item.position.x}px`,
                      top: `${item.position.y}px`,
                      width: `${item.size.width}px`,
                      height: `${item.size.height}px`,
                      backgroundImage: `url(${item.imageUrl})`,
                      backgroundSize: 'contain',
                      backgroundPosition: 'center',
                      backgroundRepeat: 'no-repeat',
                      transform: `rotate(${item.rotation}deg)`,
                      transformOrigin: 'center',
                      zIndex: item.zIndex,
                      cursor: 'move',
                      border: selectedItem && selectedItem.id === item.id ? '2px dashed #00aaff' : 'none'
                    }}
                    onMouseDown={(e) => handleMouseDown(e, item)}
                  >
                    {selectedItem && selectedItem.id === item.id && (
                      <>
                        {/* Resize handles */}
                        <div 
                          className="resize-handle nw" 
                          style={{ position: 'absolute', top: '-5px', left: '-5px', width: '10px', height: '10px', background: '#00aaff', cursor: 'nw-resize' }}
                          onMouseDown={(e) => handleResize(e, item, 'nw')}
                        ></div>
                        <div 
                          className="resize-handle ne" 
                          style={{ position: 'absolute', top: '-5px', right: '-5px', width: '10px', height: '10px', background: '#00aaff', cursor: 'ne-resize' }}
                          onMouseDown={(e) => handleResize(e, item, 'ne')}
                        ></div>
                        <div 
                          className="resize-handle sw" 
                          style={{ position: 'absolute', bottom: '-5px', left: '-5px', width: '10px', height: '10px', background: '#00aaff', cursor: 'sw-resize' }}
                          onMouseDown={(e) => handleResize(e, item, 'sw')}
                        ></div>
                        <div 
                          className="resize-handle se" 
                          style={{ position: 'absolute', bottom: '-5px', right: '-5px', width: '10px', height: '10px', background: '#00aaff', cursor: 'se-resize' }}
                          onMouseDown={(e) => handleResize(e, item, 'se')}
                        ></div>
                        
                        {/* Rotation handle */}
                        <div 
                          className="rotate-handle" 
                          style={{ position: 'absolute', top: '-20px', left: '50%', transform: 'translateX(-50%)', width: '15px', height: '15px', background: '#ff5500', borderRadius: '50%', cursor: 'grab' }}
                          onMouseDown={(e) => handleRotate(e, item)}
                        ></div>
                      </>
                    )}
                  </div>
                ))}
              </div>
            </div>
            
            <div className="outfit-summary">
              <h3>{outfit?.outfit_name || 'Custom Outfit'}</h3>
              <p>{outfit?.style_description || 'Your personalized style'}</p>
              <p className="price-tag">Total: ${outfit?.total_price?.toFixed(2) || '0.00'}</p>
              
              <div className="outfit-items-summary">
                {outfit?.items?.map((item, index) => (
                  <div className="summary-item" key={index}>
                    <span className="item-name">{item.name}</span>
                    <span className="item-price">${item.price.toFixed(2)}</span>
                  </div>
                ))}
              </div>
              
              <div className="tryon-actions">
                <button className="shop-all-button">Shop All Items</button>
                <button className="share-button">Share Look</button>
                <button className="save-button">Save Design</button>
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