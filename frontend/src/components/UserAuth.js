import React, { useState } from 'react';

const UserAuth = ({ onClose, onLogin }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    
    try {
      // This is a mock implementation - in a real app we would call an API
      if (isLogin) {
        // Mock login
        await new Promise(resolve => setTimeout(resolve, 1000));
        onLogin({ name: 'Demo User', email: email });
      } else {
        // Mock signup
        await new Promise(resolve => setTimeout(resolve, 1000));
        onLogin({ name: name, email: email });
      }
      
      onClose();
    } catch (err) {
      setError(err.message || 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-modal">
      <div className="auth-header">
        <h2>{isLogin ? 'Log In' : 'Create Account'}</h2>
        <button className="close-button" onClick={onClose}>×</button>
      </div>
      
      <div className="auth-content">
        <div className="auth-tabs">
          <button 
            className={`auth-tab ${isLogin ? 'active' : ''}`}
            onClick={() => setIsLogin(true)}
          >
            Log In
          </button>
          <button 
            className={`auth-tab ${!isLogin ? 'active' : ''}`}
            onClick={() => setIsLogin(false)}
          >
            Sign Up
          </button>
        </div>
        
        {error && <div className="auth-error">{error}</div>}
        
        <form onSubmit={handleSubmit} className="auth-form">
          {!isLogin && (
            <div className="form-group">
              <label htmlFor="name">Full Name</label>
              <input
                id="name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required={!isLogin}
                placeholder="Enter your full name"
              />
            </div>
          )}
          
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="Enter your email"
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="Enter your password"
            />
          </div>
          
          <button 
            type="submit" 
            className="auth-button"
            disabled={isLoading}
          >
            {isLoading 
              ? 'Processing...' 
              : isLogin ? 'Log In' : 'Create Account'
            }
          </button>
        </form>
        
        <div className="social-auth">
          <p>Or continue with</p>
          <div className="social-buttons">
            <button className="social-button google">
              <span>Google</span>
            </button>
            <button className="social-button facebook">
              <span>Facebook</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UserAuth; 