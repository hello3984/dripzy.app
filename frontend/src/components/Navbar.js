import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import Logo from '../logo.svg';
import './Navbar.css';

const Navbar = ({ user, onLogin, onLogout }) => {
  const [menuOpen, setMenuOpen] = useState(false);
  // eslint-disable-next-line no-unused-vars
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
        The Most Advanced AI Stylist—Now at Your Fingertips
      </div>
      
      <nav className="navbar">
        <div className="navbar-container">
          <Link to="/" className="navbar-logo">
            <img src={Logo} alt="Dripzy" />
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
                <a href="#generate" data-tooltip="Create your AI-powered outfit">TRY IT</a>
              </li>
              <li className="menu-item">
                <Link to="/theme-collage" data-tooltip="Create themed outfit collages">THEME COLLAGES</Link>
              </li>
              <li className="menu-item dropdown">
                <a href="#more" data-tooltip="Learn more about Dripzy">MORE</a>
                <div className="dropdown-menu">
                  <a href="#pricing">Pricing</a>
                  <a href="#how">How It Works</a>
                  <a href="#about">About Us</a>
                </div>
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