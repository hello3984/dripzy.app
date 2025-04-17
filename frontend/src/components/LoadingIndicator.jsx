import React from 'react';

const LoadingIndicator = ({ message = 'Loading...' }) => {
  return (
    <div className="loading-indicator">
      <div className="spinner"></div>
      {message && <p className="loading-message">{message}</p>}
      
      <style jsx>{`
        .loading-indicator {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
        }
        
        .spinner {
          border: 4px solid rgba(0, 0, 0, 0.1);
          width: 40px;
          height: 40px;
          border-radius: 50%;
          border-left-color: #6c4ed9;
          animation: spin 1s linear infinite;
        }
        
        .loading-message {
          margin-top: 1rem;
          color: #666;
          font-size: 0.9rem;
        }
        
        @keyframes spin {
          0% {
            transform: rotate(0deg);
          }
          100% {
            transform: rotate(360deg);
          }
        }
      `}</style>
    </div>
  );
};

export default LoadingIndicator; 