import React, { useState } from 'react';
import { Link } from 'react-router-dom';

const Navbar = ({ user, onLogin, onLogout }) => {
  const [menuOpen, setMenuOpen] = useState(false);
  const [showAuthModal, setShowAuthModal] = useState(false);
  
  const toggleMenu = () => {
    setMenuOpen(!menuOpen);
  };
  
  const handleLogin = () => {
    setShowAuthModal(true);
    setMenuOpen(false);
  };
  
  const handleLogout = () => {
    onLogout();
    setMenuOpen(false);
  };
  
  return (
    <nav className="navbar">
      <div className="navbar-container">
        <div className="navbar-logo">
          <span className="logo-icon">👗</span>
          <span className="logo-text">Dripzy</span>
        </div>
        
        <div className="navbar-search">
          <input 
            type="text" 
            placeholder="Search for styles, items, or brands..." 
            className="search-input"
          />
          <button className="search-button">🔍</button>
        </div>
        
        <div className={`navbar-menu ${menuOpen ? 'active' : ''}`}>
          <button 
            className="menu-toggle"
            onClick={toggleMenu}
            aria-label="Toggle menu"
          >
            <span className="menu-icon"></span>
          </button>
          
          <ul className="menu-items">
            <li className="menu-item">
              <a href="#styles">Explore Styles</a>
            </li>
            <li className="menu-item">
              <a href="#how-it-works">How It Works</a>
            </li>
            <li className="menu-item">
              <a href="#pricing">Pricing</a>
            </li>
            {user ? (
              <>
                <li className="menu-item user-menu">
                  <button className="user-button">
                    <span className="user-avatar">
                      {user.name.charAt(0)}
                    </span>
                    <span className="user-name">{user.name}</span>
                  </button>
                  <div className="user-dropdown">
                    <a href="#profile">My Profile</a>
                    <a href="#saved">Saved Outfits</a>
                    <a href="#settings">Settings</a>
                    <button onClick={handleLogout}>Log Out</button>
                  </div>
                </li>
              </>
            ) : (
              <li className="menu-item auth-buttons">
                <button 
                  className="login-button"
                  onClick={handleLogin}
                >
                  Log In
                </button>
                <button 
                  className="signup-button"
                  onClick={handleLogin}
                >
                  Sign Up
                </button>
              </li>
            )}
          </ul>
        </div>
      </div>
      
      {/* This would be conditionally rendered using the showAuthModal state */}
      {/* For now we'll just leave it commented out */}
      {/* {showAuthModal && (
        <UserAuth 
          onClose={() => setShowAuthModal(false)}
          onLogin={(userData) => {
            onLogin(userData);
            setShowAuthModal(false);
          }}
        />
      )} */}
    </nav>
  );
};

export default Navbar; 