import React, { useState, useRef, useEffect } from 'react';
import './VirtualTryOn.css';

const VirtualTryOn = ({ onComplete }) => {
  const [userPhoto, setUserPhoto] = useState(null);
  const [avatarImage, setAvatarImage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState('upload'); // 'upload', 'preview', 'avatar'
  const fileInputRef = useRef(null);
  
  // Check if iOS Safari
  const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
  const isSafari = /^((?!chrome|android).)*safari/i.test(navigator.userAgent);

  // Handle file selection
  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (event) => {
      setUserPhoto(event.target.result);
      setStep('preview');
    };
    reader.readAsDataURL(file);
  };

  // Handle camera access
  const handleCameraClick = async () => {
    if (isIOS && isSafari) {
      // For iOS Safari, just open the file picker with capture attribute
      fileInputRef.current.setAttribute('capture', 'user');
      fileInputRef.current.click();
    } else {
      try {
        // For other browsers, request camera permission first
        await navigator.mediaDevices.getUserMedia({ video: true });
        fileInputRef.current.setAttribute('capture', 'user');
        fileInputRef.current.click();
      } catch (err) {
        console.error("Camera permission denied:", err);
        alert("Please allow camera access to use this feature");
      }
    }
  };

  // Handle gallery access
  const handleGalleryClick = () => {
    // Remove capture attribute to access photo gallery
    fileInputRef.current.removeAttribute('capture');
    fileInputRef.current.click();
  };

  // Generate avatar from uploaded photo
  const generateAvatar = async () => {
    setLoading(true);
    
    try {
      // In a real implementation, you would make an API call to a service like Ready Player Me
      // For now, we'll simulate the API call with a timeout
      setTimeout(() => {
        // This is where we would normally set the avatar from the API response
        // For demo purposes, we're just using the user's photo as a placeholder
        setAvatarImage(userPhoto);
        setStep('avatar');
        setLoading(false);
      }, 2000);
      
      // Actual API implementation would look something like this:
      /*
      const response = await fetch('https://api.example.com/create-avatar', {
        method: 'POST',
        body: JSON.stringify({ image: userPhoto }),
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      const data = await response.json();
      setAvatarImage(data.avatarUrl);
      */
    } catch (error) {
      console.error('Error generating avatar:', error);
      setLoading(false);
    }
  };

  // Reset and start over
  const handleReset = () => {
    setUserPhoto(null);
    setAvatarImage(null);
    setStep('upload');
  };

  // Continue to outfit selection
  const handleContinue = () => {
    if (onComplete) {
      onComplete(avatarImage);
    }
  };

  return (
    <div className="virtual-try-on">
      <h2>Virtual Try-On</h2>
      
      {step === 'upload' && (
        <div className="upload-section">
          <div className="upload-container">
            <h3>Let's see what you look like</h3>
            <p>A face photo will help us create a more accurate try-on experience for you.</p>
            
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileSelect}
              accept="image/*"
              style={{ display: 'none' }}
            />
            
            <div className="upload-buttons">
              <button 
                className="camera-button"
                onClick={handleCameraClick}
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path>
                  <circle cx="12" cy="13" r="4"></circle>
                </svg>
                Take Selfie
              </button>
              
              <button 
                className="gallery-button"
                onClick={handleGalleryClick}
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                  <circle cx="8.5" cy="8.5" r="1.5"></circle>
                  <polyline points="21 15 16 10 5 21"></polyline>
                </svg>
                Gallery
              </button>
            </div>
            
            <button 
              className="default-avatar-button"
              onClick={() => setStep('avatar')}
            >
              Use Default Avatar
            </button>
          </div>
          
          <div className="example-container">
            <div className="example-image">
              <img src="/images/avatar-example.jpg" alt="Avatar Example" />
            </div>
            <p>Your photo will be used to create a digital avatar for try-on</p>
          </div>
        </div>
      )}
      
      {step === 'preview' && (
        <div className="preview-section">
          <h3>Your Photo</h3>
          
          <div className="photo-preview">
            <img src={userPhoto} alt="Your uploaded" />
          </div>
          
          <div className="preview-buttons">
            <button 
              className="secondary-button"
              onClick={handleReset}
            >
              Try Another Photo
            </button>
            
            <button 
              className="primary-button"
              onClick={generateAvatar}
              disabled={loading}
            >
              {loading ? 'Creating Avatar...' : 'Create My Avatar'}
            </button>
          </div>
        </div>
      )}
      
      {step === 'avatar' && (
        <div className="avatar-section">
          <h3>Your Avatar</h3>
          
          <div className="avatar-preview">
            {avatarImage && (
              <div className="avatar-image">
                <img src={avatarImage} alt="Your avatar" />
              </div>
            )}
            
            {!avatarImage && (
              <div className="default-avatar">
                <img src="/images/default-avatar.jpg" alt="Default avatar" />
              </div>
            )}
          </div>
          
          <div className="avatar-buttons">
            <button 
              className="change-avatar-button"
              onClick={handleReset}
            >
              Change Avatar
            </button>
            
            <button 
              className="continue-button"
              onClick={handleContinue}
            >
              Continue to Outfits
            </button>
          </div>
          
          <div className="avatar-info">
            <p>
              Your avatar is ready! Now you can try on different outfits and styles.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default VirtualTryOn; 