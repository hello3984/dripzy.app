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
    <>
      <div className="announcement-banner">
        Dripzy is now part of the LVMH Startup Acceleration Program at La Maison des Startups
      </div>
      
      <nav className="navbar">
        <div className="navbar-container">
          <Link to="/" className="navbar-logo">
            <span className="logo-text">dripzy</span>
          </Link>
          
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
                <Link to="/" data-tooltip="Explore AI fashion">FEATURES</Link>
              </li>
              <li className="menu-item">
                <a href="#generate" data-tooltip="Create your AI-powered outfit">SHOWCASE</a>
              </li>
              <li className="menu-item">
                <a href="#pricing" data-tooltip="View our pricing options">PRICING</a>
              </li>
              <li className="menu-item">
                <a href="#how" data-tooltip="Learn about our AI fashion technology">HOW TO USE</a>
              </li>
              <li className="menu-item">
                <a href="#about" data-tooltip="Learn about Dripzy">ABOUT</a>
              </li>
            </ul>
          </div>
          
          <div className="auth-actions">
            {user ? (
              <div className="user-menu">
                <button className="user-button" data-tooltip="Your account options">
                  <span className="user-name">{user.name}</span>
                </button>
                <div className="user-dropdown">
                  <a href="#profile" data-tooltip="View your profile">Profile</a>
                  <a href="#saved" data-tooltip="See your saved outfits">Saved</a>
                  <button onClick={handleLogout} data-tooltip="Sign out of your account">Log Out</button>
                </div>
              </div>
            ) : (
              <div className="auth-buttons">
                <button 
                  className="sign-in"
                  onClick={handleLogin}
                  data-tooltip="Sign in to your account"
                >
                  Sign In
                </button>
                <button 
                  className="try-for-free"
                  onClick={handleLogin}
                  data-tooltip="Try Dripzy for free"
                >
                  Try for Free
                </button>
              </div>
            )}
          </div>
        </div>
      </nav>
    </>
  );
};

export default Navbar; 