import React, { useState, useEffect, useRef } from 'react';
import { getAvatarOptions, uploadUserImage, generateTryOn } from '../services/api';
import VirtualTryOn from './VirtualTryOn';

const TryOnPage = () => {
  const [avatars, setAvatars] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tryOnMethod, setTryOnMethod] = useState('avatar'); // 'avatar' or 'upload'
  const [selectedAvatar, setSelectedAvatar] = useState(null);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [uploadedImage, setUploadedImage] = useState(null);
  const [uploadedImageId, setUploadedImageId] = useState(null);
  const [tryOnResult, setTryOnResult] = useState(null);
  const [tryOnLoading, setTryOnLoading] = useState(false);
  const fileInputRef = useRef(null);
  
  // Demo products
  const demoProducts = [
    {
      id: 'p1',
      name: 'Fringe Crop Top',
      brand: 'ASOS',
      image_url: 'https://via.placeholder.com/300x400?text=Fringe+Crop+Top',
      price: 45.99
    },
    {
      id: 'p5',
      name: 'Casual White T-Shirt',
      brand: 'GAP',
      image_url: 'https://via.placeholder.com/300x400?text=White+T-Shirt',
      price: 24.99
    },
    {
      id: 'p6',
      name: 'Black Skinny Jeans',
      brand: 'Levi\'s',
      image_url: 'https://via.placeholder.com/300x400?text=Black+Jeans',
      price: 59.99
    },
    {
      id: 'p7',
      name: 'White Sneakers',
      brand: 'Nike',
      image_url: 'https://via.placeholder.com/300x400?text=White+Sneakers',
      price: 89.99
    }
  ];

  useEffect(() => {
    // Fetch avatar options when component mounts
    fetchAvatars();
  }, []);

  const fetchAvatars = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getAvatarOptions();
      setAvatars(data);
      if (data.length > 0) {
        setSelectedAvatar(data[0].id); // Select first avatar by default
      }
    } catch (err) {
      console.error('Error fetching avatars:', err);
      setError('Failed to fetch avatars. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    // Preview image
    const reader = new FileReader();
    reader.onload = (event) => {
      setUploadedImage(event.target.result);
    };
    reader.readAsDataURL(file);
    
    // Upload the image
    handleImageUpload(file);
  };

  const handleImageUpload = async (file) => {
    try {
      setLoading(true);
      setError(null);
      const data = await uploadUserImage(file);
      setUploadedImageId(data.image_id);
    } catch (err) {
      console.error('Error uploading image:', err);
      setError('Failed to upload image. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const handleTryOn = async () => {
    if (!selectedProduct) {
      setError('Please select a product to try on.');
      return;
    }
    
    if (tryOnMethod === 'avatar' && !selectedAvatar) {
      setError('Please select an avatar.');
      return;
    }
    
    if (tryOnMethod === 'upload' && !uploadedImageId) {
      setError('Please upload an image first.');
      return;
    }
    
    try {
      setTryOnLoading(true);
      setError(null);
      
      const tryOnRequest = {
        product_id: selectedProduct,
        avatar_id: tryOnMethod === 'avatar' ? selectedAvatar : undefined,
        user_image_id: tryOnMethod === 'upload' ? uploadedImageId : undefined
      };
      
      const result = await generateTryOn(tryOnRequest);
      setTryOnResult(result);
    } catch (err) {
      console.error('Error generating try-on:', err);
      setError('Failed to generate try-on. Please try again later.');
    } finally {
      setTryOnLoading(false);
    }
  };

  const handleReset = () => {
    setTryOnResult(null);
    setSelectedProduct(null);
    if (tryOnMethod === 'upload') {
      setUploadedImage(null);
      setUploadedImageId(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  return (
    <div className="tryon-page">
      <div className="container">
        <h1>Virtual Try-On</h1>
        <p className="subtitle">See how clothes look on you before buying!</p>
        
        {error && <div className="error-message">{error}</div>}
        
        <div className="tryon-layout">
          <div className="tryon-options">
            <div className="tryon-method-toggle">
              <button 
                className={`method-btn ${tryOnMethod === 'avatar' ? 'active' : ''}`}
                onClick={() => setTryOnMethod('avatar')}
              >
                Use Avatar
              </button>
              <button 
                className={`method-btn ${tryOnMethod === 'upload' ? 'active' : ''}`}
                onClick={() => setTryOnMethod('upload')}
              >
                Upload Photo
              </button>
            </div>
            
            {tryOnMethod === 'avatar' ? (
              <div className="avatar-selector">
                <h3>Select Avatar</h3>
                {loading ? (
                  <div className="loading">Loading avatars...</div>
                ) : (
                  <div className="avatars-grid">
                    {avatars.map(avatar => (
                      <div 
                        key={avatar.id}
                        className={`avatar-card ${selectedAvatar === avatar.id ? 'selected' : ''}`}
                        onClick={() => setSelectedAvatar(avatar.id)}
                      >
                        <img 
                          src={avatar.image_url || 'https://via.placeholder.com/150x200?text=Avatar'} 
                          alt={avatar.name} 
                          className="avatar-image"
                        />
                        <div className="avatar-info">
                          <h4>{avatar.name}</h4>
                          <p>{avatar.description}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="image-uploader">
                <h3>Upload Your Photo</h3>
                <p>Upload a front-facing photo of yourself for the best results.</p>
                
                <div className="upload-area">
                  {uploadedImage ? (
                    <div className="preview-container">
                      <img src={uploadedImage} alt="Uploaded" className="preview-image" />
                      <button 
                        className="remove-image-btn"
                        onClick={() => {
                          setUploadedImage(null);
                          setUploadedImageId(null);
                          if (fileInputRef.current) {
                            fileInputRef.current.value = '';
                          }
                        }}
                      >
                        Remove
                      </button>
                    </div>
                  ) : (
                    <div className="upload-prompt">
                      <div className="upload-icon">📷</div>
                      <p>Click to select a photo or drag and drop</p>
                      <input
                        type="file"
                        accept="image/*"
                        onChange={handleFileSelect}
                        ref={fileInputRef}
                        className="file-input"
                      />
                    </div>
                  )}
                </div>
                
                <div className="image-guidelines">
                  <h4>For best results:</h4>
                  <ul>
                    <li>Use a well-lit, front-facing photo</li>
                    <li>Stand in a neutral pose</li>
                    <li>Use a plain background</li>
                    <li>Wear fitted clothing</li>
                  </ul>
                </div>
              </div>
            )}
            
            <div className="product-selector">
              <h3>Select Product to Try On</h3>
              <div className="demo-products">
                {demoProducts.map(product => (
                  <div 
                    key={product.id}
                    className={`product-tile ${selectedProduct === product.id ? 'selected' : ''}`}
                    onClick={() => setSelectedProduct(product.id)}
                  >
                    <img 
                      src={product.image_url} 
                      alt={product.name} 
                      className="product-thumb"
                    />
                    <div className="product-info">
                      <h4>{product.name}</h4>
                      <p>{product.brand} - ${product.price.toFixed(2)}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            <div className="tryon-actions">
              <button 
                className="tryon-button"
                onClick={handleTryOn}
                disabled={tryOnLoading}
              >
                {tryOnLoading ? 'Generating...' : 'Try On This Item'}
              </button>
              
              {tryOnResult && (
                <button className="reset-button" onClick={handleReset}>
                  Try Another Item
                </button>
              )}
            </div>
          </div>
          
          <div className="tryon-result">
            {tryOnLoading ? (
              <div className="loading-tryon">
                <div className="loading-spinner"></div>
                <p>Generating your virtual try-on...</p>
                <p className="loading-message">This may take a few seconds.</p>
              </div>
            ) : tryOnResult ? (
              <div className="result-container">
                <div className="result-header">
                  <h3>Try-On Result</h3>
                  <p>{tryOnResult.product_name}</p>
                </div>
                
                <div className="comparison-view">
                  <div className="original-image">
                    <h4>Original Product</h4>
                    <img 
                      src={tryOnResult.original_image_url} 
                      alt="Original product" 
                      className="original-img"
                    />
                  </div>
                  
                  <div className="tryon-image">
                    <h4>Virtual Try-On</h4>
                    <img 
                      src={tryOnResult.tryon_image_url} 
                      alt="Try-on result" 
                      className="tryon-img"
                    />
                  </div>
                </div>
                
                <div className="result-footer">
                  <button className="share-btn">Share</button>
                  <button className="save-btn">Save to Favorites</button>
                </div>
              </div>
            ) : (
              <div className="tryon-placeholder">
                <VirtualTryOn />
                <p className="placeholder-text">
                  {tryOnMethod === 'avatar' 
                    ? 'Select an avatar and a product to see how it looks'
                    : 'Upload your photo and select a product to try on'
                  }
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TryOnPage; 