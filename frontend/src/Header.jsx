import React from 'react';
import { Link } from 'react-router-dom';

const Header = () => {
  return (
    <>
      <div className="announcement-banner">
        Dripzy is now part of exciting AI fashion innovation
      </div>
      
      <header className="header">
        <div className="logo">dripzy</div>
        <nav className="nav-links">
          <Link to="/features">FEATURES</Link>
          <Link to="/showcase">SHOWCASE</Link>
          <Link to="/pricing">PRICING</Link>
          <Link to="/how-to-use">HOW TO USE</Link>
          <Link to="/about">ABOUT</Link>
        </nav>
        <div className="auth-buttons">
          <Link to="/signin" className="button outline-button">Sign In</Link>
          <Link to="/signup" className="button secondary-button">Try for Free</Link>
        </div>
      </header>
    </>
  );
};

export default Header; 