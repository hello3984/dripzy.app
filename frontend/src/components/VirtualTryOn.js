import React, { useState, useRef } from 'react';
import './VirtualTryOn.css';

const VirtualTryOn = ({ onComplete }) => {
  const [userPhoto, setUserPhoto] = useState(null);
  const [avatarImage, setAvatarImage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState('upload'); // 'upload', 'preview', 'avatar'
  const fileInputRef = useRef(null);

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

  // Trigger file input click
  const handleUploadClick = () => {
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
            
            <button 
              className="upload-button"
              onClick={handleUploadClick}
            >
              Upload Selfie
            </button>
            
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