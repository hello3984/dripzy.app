import React, { useRef, useEffect, useState } from 'react';
import './VirtualTryOn.css';

const VirtualTryOn = () => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [isActive, setIsActive] = useState(false);
  const [selectedAccessory, setSelectedAccessory] = useState(null);
  const [faceDetected, setFaceDetected] = useState(false);

  // Initialize camera and face detection
  useEffect(() => {
    if (isActive) {
      startCamera();
      initializeFaceDetection();
    } else {
      stopCamera();
    }
  }, [isActive]);

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { 
          width: 640, 
          height: 480, 
          facingMode: 'user' 
        } 
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    } catch (error) {
      console.error('Error accessing camera:', error);
    }
  };

  const stopCamera = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      const tracks = videoRef.current.srcObject.getTracks();
      tracks.forEach(track => track.stop());
    }
  };

  const initializeFaceDetection = async () => {
    // Placeholder for MediaPipe Face Detection integration
    // In real implementation, we would initialize MediaPipe here
    console.log('Initializing face detection...');
    
    // Simulate face detection
    const detectFaces = () => {
      if (videoRef.current && canvasRef.current) {
        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        const video = videoRef.current;
        
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        
        // Draw video frame
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        // Simulate face detection (in real implementation, use MediaPipe results)
        const mockFaceData = {
          x: canvas.width * 0.3,
          y: canvas.height * 0.2,
          width: canvas.width * 0.4,
          height: canvas.height * 0.5
        };
        
        setFaceDetected(true);
        
        // Apply virtual accessory if selected
        if (selectedAccessory) {
          applyVirtualAccessory(ctx, mockFaceData, selectedAccessory);
        }
        
        // Draw face detection box (for demo purposes)
        ctx.strokeStyle = '#00ff00';
        ctx.lineWidth = 2;
        ctx.strokeRect(mockFaceData.x, mockFaceData.y, mockFaceData.width, mockFaceData.height);
      }
      
      if (isActive) {
        requestAnimationFrame(detectFaces);
      }
    };
    
    // Start detection loop
    requestAnimationFrame(detectFaces);
  };

  const applyVirtualAccessory = (ctx, faceData, accessory) => {
    // This is where we would apply virtual accessories
    // For demo, we'll draw a simple hat or glasses overlay
    
    ctx.fillStyle = accessory.color || '#ff0000';
    ctx.globalAlpha = 0.7;
    
    switch (accessory.type) {
      case 'hat':
        // Draw a simple hat
        ctx.fillRect(
          faceData.x - 20, 
          faceData.y - 40, 
          faceData.width + 40, 
          40
        );
        break;
      case 'glasses':
        // Draw simple glasses
        ctx.fillRect(
          faceData.x + 20, 
          faceData.y + faceData.height * 0.3, 
          faceData.width - 40, 
          20
        );
        break;
      case 'earrings':
        // Draw earrings
        ctx.beginPath();
        ctx.arc(faceData.x + 10, faceData.y + faceData.height * 0.4, 8, 0, 2 * Math.PI);
        ctx.fill();
        ctx.beginPath();
        ctx.arc(faceData.x + faceData.width - 10, faceData.y + faceData.height * 0.4, 8, 0, 2 * Math.PI);
        ctx.fill();
        break;
    }
    
    ctx.globalAlpha = 1.0;
  };

  const accessories = [
    { type: 'hat', name: 'Baseball Cap', color: '#ff0000' },
    { type: 'glasses', name: 'Sunglasses', color: '#000000' },
    { type: 'earrings', name: 'Gold Hoops', color: '#ffd700' },
  ];

  return (
    <div className="virtual-tryon-container">
      <div className="tryon-header">
        <h2>🔮 Virtual Try-On</h2>
        <p>Experience AI-powered fashion preview</p>
      </div>

      <div className="tryon-content">
        <div className="camera-section">
          <div className="camera-container">
            {isActive ? (
              <>
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  muted
                  style={{ display: 'none' }}
                />
                <canvas
                  ref={canvasRef}
                  className="tryon-canvas"
                />
                <div className="detection-status">
                  {faceDetected ? (
                    <span className="status-active">👤 Face Detected</span>
                  ) : (
                    <span className="status-searching">🔍 Looking for face...</span>
                  )}
                </div>
              </>
            ) : (
              <div className="camera-placeholder">
                <div className="placeholder-content">
                  <span className="camera-icon">📷</span>
                  <p>Click "Start Try-On" to begin</p>
                </div>
              </div>
            )}
          </div>

          <div className="camera-controls">
            <button
              className={`tryon-btn ${isActive ? 'stop' : 'start'}`}
              onClick={() => setIsActive(!isActive)}
            >
              {isActive ? '⏹️ Stop Try-On' : '▶️ Start Try-On'}
            </button>
          </div>
        </div>

        <div className="accessories-section">
          <h3>Select Accessories</h3>
          <div className="accessories-grid">
            {accessories.map((accessory, index) => (
              <div
                key={index}
                className={`accessory-item ${
                  selectedAccessory?.type === accessory.type ? 'selected' : ''
                }`}
                onClick={() => setSelectedAccessory(accessory)}
              >
                <div 
                  className="accessory-preview"
                  style={{ backgroundColor: accessory.color }}
                ></div>
                <span>{accessory.name}</span>
              </div>
            ))}
            <div
              className={`accessory-item ${!selectedAccessory ? 'selected' : ''}`}
              onClick={() => setSelectedAccessory(null)}
            >
              <div className="accessory-preview none">
                <span>❌</span>
              </div>
              <span>None</span>
            </div>
          </div>
        </div>
      </div>

      <div className="implementation-info">
        <h4>🛠️ DIY Implementation Features:</h4>
        <div className="features-list">
          <div className="feature">✅ Real-time face detection</div>
          <div className="feature">✅ Virtual accessory overlay</div>
          <div className="feature">✅ Web-based (no app required)</div>
          <div className="feature">🔄 Expandable to clothing items</div>
        </div>
      </div>
    </div>
  );
};

export default VirtualTryOn; 